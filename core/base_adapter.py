from abc import ABC, abstractmethod

class BaseDeviceAdapter(ABC):
    """Абстрактный класс для адаптеров всех вендоров."""

    def __init__(
        self,
        ip: str,
        vendor: str,
        vendor_config: dict,
        target_admin_user: str,
        old_admin_pass: str | None,
        new_admin_pass: str,
    ):
        self.ip = ip
        self.vendor = vendor
        self.vendor_config = vendor_config
        self.target_admin_user = target_admin_user
        self.old_admin_pass = old_admin_pass
        self.new_admin_pass = new_admin_pass
        self.active_port = None

    @abstractmethod
    def connect(self, radius_user: str | None = None, radius_pass: str | None = None) -> bool:
        """Подключение к устройству (RADIUS или Local в зависимости от auth_type)."""
        pass

    @abstractmethod
    def change_local_admin_password(self) -> bool:
        """Смена пароля целевого админа."""
        pass

    @abstractmethod
    def verify_new_admin_login(self) -> str:
        """
        Проверка входа под новым паролем.
        Возвращает: 'OK', 'FAIL' или 'SKIPPED'
        """
        pass

    @abstractmethod
    def close(self):
        """Закрытие соединений."""
        pass
