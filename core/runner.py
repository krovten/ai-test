from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    VENDOR_CONFIG,
    RADIUS_USER,
    RADIUS_PASS,
    TARGET_ADMIN_USER,
    get_vendor_by_model,
    get_passwords_for_vendor,
)
from core.factory import get_adapter_class
from utils.logger import logger
from utils.network import ping_host

def process_single_device(ip: str, model: str, retries_left: int = 1) -> dict:
    result = {
        "IP": ip,
        "MODEL": model,
        "VENDOR": "UNKNOWN",
        "PING": "FAIL",
        "AUTH_LOGIN": "FAIL",
        "PASSWORD_CHANGED": "FAIL",
        "NEW_ADMIN_LOGIN": "FAIL",
        "STATUS": "FAIL",
    }

    if not ping_host(ip):
        logger.warning(f"[{ip}] Ping недоступен.")
        result["STATUS"] = "HOST_UNREACHABLE"
        return result
    result["PING"] = "OK"

    vendor = get_vendor_by_model(model)
    if not vendor:
        result["STATUS"] = "UNKNOWN_MODEL"
        return result

    result["VENDOR"] = vendor
    vendor_cfg = VENDOR_CONFIG[vendor]

    adapter_cls = get_adapter_class(vendor)
    if not adapter_cls:
        logger.error(f"[{ip}] Модуль-адаптер для вендора '{vendor}' не загружен!")
        result["STATUS"] = "MODULE_NOT_FOUND"
        return result

    old_pass, new_pass = get_passwords_for_vendor(vendor)
    adapter = adapter_cls(
        ip=ip,
        vendor=vendor,
        vendor_config=vendor_cfg,
        target_admin_user=TARGET_ADMIN_USER,
        old_admin_pass=old_pass,
        new_admin_pass=new_pass,
    )

    try:
        # 1. Авторизация
        if not adapter.connect(RADIUS_USER, RADIUS_PASS):
            if retries_left > 0:
                logger.info(f"[{ip}] Повторная попытка (Retry)...")
                adapter.close()
                return process_single_device(ip, model, retries_left - 1)
            result["STATUS"] = "AUTH_FAILED"
            return result
        result["AUTH_LOGIN"] = "OK"

        # 2. Смена пароля
        if not adapter.change_local_admin_password():
            result["STATUS"] = "CHANGE_PASSWORD_FAILED"
            return result
        result["PASSWORD_CHANGED"] = "OK"

        # Закрываем сессию смены пароля
        adapter.close()

        # 3. Верификация нового входа
        verify_status = adapter.verify_new_admin_login()
        result["NEW_ADMIN_LOGIN"] = verify_status

        if verify_status in ["OK", "SKIPPED"]:
            result["STATUS"] = "SUCCESS"
            logger.info(f"[{ip}] Успешно обработано ({vendor}/{model})")
        else:
            result["STATUS"] = "VERIFY_FAILED"

    except Exception as e:
        logger.error(f"[{ip}] Необработанная ошибка: {e}")
        result["STATUS"] = "ERROR"
    finally:
        adapter.close()

    return result


def run_job(devices: list[tuple[str, str]], max_workers: int = 10) -> list[dict]:
    logger.info(f"Запуск обработки {len(devices)} устройств в {max_workers} потоков...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_device, ip, model): ip
            for ip, model in devices
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x["IP"])
    return results
