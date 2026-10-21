import importlib
import pkgutil
from typing import Type
from core.base_adapter import BaseDeviceAdapter
from utils.logger import logger

ADAPTER_REGISTRY: dict[str, Type[BaseDeviceAdapter]] = {}

def register_adapter(vendor_name: str):
    """Декоратор для автоматической регистрации адаптера вендора."""
    def decorator(cls: Type[BaseDeviceAdapter]):
        ADAPTER_REGISTRY[vendor_name.lower()] = cls
        return cls
    return decorator

def load_modules():
    """Динамически импортирует все Python-модули из каталога modules/."""
    import modules
    for _, module_name, _ in pkgutil.iter_modules(modules.__path__):
        full_module_name = f"modules.{module_name}"
        try:
            importlib.import_module(full_module_name)
            logger.debug(f"Загружен модуль адаптера: {full_module_name}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модуля {full_module_name}: {e}")

def get_adapter_class(vendor_name: str) -> Type[BaseDeviceAdapter] | None:
    """Возвращает класс адаптера по имени вендора."""
    return ADAPTER_REGISTRY.get(vendor_name.lower())
