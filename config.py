
import yaml
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Основные переменные
RADIUS_USER = os.getenv("RADIUS_USER")
RADIUS_PASS = os.getenv("RADIUS_PASS")
TARGET_ADMIN_USER = os.getenv("TARGET_ADMIN_USER", "admin")

# Загрузка YAML-конфигурации вендоров
CONFIG_FILE = "device_config.yaml"
if not os.path.exists(CONFIG_FILE):
    print(f"[PRE-FLIGHT CRITICAL] Файл конфигурации вендоров {CONFIG_FILE} не найден!")
    sys.exit(1)

try:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        VENDOR_CONFIG = yaml.safe_load(f) or {}
except yaml.YAMLError as e:
    print(f"[PRE-FLIGHT CRITICAL] Ошибка чтения YAML-файла {CONFIG_FILE}: {e}")
    sys.exit(1)


def get_vendor_by_model(model_name: str) -> str | None:
    """Находит имя вендора по названию модели."""
    model_name_lower = model_name.lower()
    for vendor, data in VENDOR_CONFIG.items():
        models = [m.lower() for m in data.get("models", [])]
        if model_name_lower in models:
            return vendor
    return None


def get_passwords_for_vendor(vendor: str) -> tuple[str | None, str | None]:
    """Возвращает старый и новый пароли из .env для конкретного вендора."""
    vendor_upper = vendor.upper()
    old_pass = os.getenv(f"OLD_ADMIN_PASS_{vendor_upper}")
    new_pass = os.getenv(f"NEW_ADMIN_PASS_{vendor_upper}")
    return old_pass, new_pass


def validate_environment(devices_csv_path: str = "devices.csv") -> list[tuple[str, str]]:
    """
    Строгая предстартовая проверка (Pre-flight Check).
    Проверяет валидность устройств, моделей, конфигов и наличие паролей в .env.
    """
    errors: list[str] = []

    if not os.path.exists(devices_csv_path):
        print(f"[PRE-FLIGHT CRITICAL] Файл устройств {devices_csv_path} не найден!")
        sys.exit(1)

    # 1. Чтение CSV и парсинг моделей
    parsed_devices = []
    with open(devices_csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for idx, line in enumerate(lines[1:], start=2):
            line = line.strip()
            if not line:
                continue
            parts = line.split(";")
            if len(parts) < 2:
                errors.append(f"Строка {idx}: неверный формат (ожидается ip;model)")
                continue

            ip, model = parts[0].strip(), parts[1].strip()
            parsed_devices.append((ip, model))

    if not parsed_devices and not errors:
        errors.append("Файл devices.csv пуст.")

    # 2. Проверка соответствия моделей и наличия паролей для найденных вендоров
    used_vendors = set()

    for ip, model in parsed_devices:
        vendor = get_vendor_by_model(model)
        if not vendor:
            errors.append(
                f"[{ip}] Модель '{model}' не найдена ни у одного вендора в {CONFIG_FILE}"
            )
        else:
            used_vendors.add(vendor)

    # 3. Проверка паролей для каждого используемого вендора
    for vendor in used_vendors:
        v_config = VENDOR_CONFIG.get(vendor, {})
        auth_type = v_config.get("auth_type", "local")

        old_pass, new_pass = get_passwords_for_vendor(vendor)

        if not new_pass:
            errors.append(
                f"В .env отсутствует NEW_ADMIN_PASS_{vendor.upper()} для вендора '{vendor}'"
            )

        if auth_type == "local" and not old_pass:
            errors.append(
                f"В .env отсутствует OLD_ADMIN_PASS_{vendor.upper()} для вендора "
                f"'{vendor}' (auth_type=local)"
            )

        if auth_type == "radius":
            if not RADIUS_USER or not RADIUS_PASS:
                errors.append(
                    f"Для вендора '{vendor}' требуется RADIUS авторизация, "
                    "но RADIUS_USER/RADIUS_PASS не заданы в .env"
                )

    if errors:
        print("\n=== [PRE-FLIGHT VALIDATION FAILED] ===")
        for err in errors:
            print(f" - {err}")
        print("Скрипт остановлен. Исправьте ошибки конфигурации перед запуском!\n")
        sys.exit(1)

    return parsed_devices
