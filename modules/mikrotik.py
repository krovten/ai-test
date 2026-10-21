import paramiko
import time
from core.base_adapter import BaseDeviceAdapter
from core.factory import register_adapter
from utils.network import check_port
from utils.logger import logger

@register_adapter("mikrotik")
class MikroTikAdapter(BaseDeviceAdapter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssh_client = None

    def _find_working_port(self) -> int | None:
        ports = self.vendor_config.get("ports", [22])
        for p in ports:
            if check_port(self.ip, p):
                return p
        return None

    def _escape_mikrotik_string(self, val: str) -> str:
        if not val:
            return ""
        val = val.replace("\\", "\\\\")
        val = val.replace('"', '\\"')
        val = val.replace("$", "\\$")
        val = val.replace(";", "\\;")
        return val

    def connect(self, radius_user: str | None = None, radius_pass: str | None = None) -> bool:
        auth_type = self.vendor_config.get("auth_type", "local")

        self.active_port = self._find_working_port()
        if not self.active_port:
            logger.error(f"[{self.ip}] Все порты вендора закрыты.")
            return False

        if auth_type == "radius":
            login_user = radius_user
            login_pass = radius_pass
        else:
            login_user = self.target_admin_user
            login_pass = self.old_admin_pass

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.ip,
                port=self.active_port,
                username=login_user,
                password=login_pass,
                timeout=10,
                look_for_keys=False,
                allow_agent=False,
            )
            self.ssh_client = ssh
            logger.debug(f"[{self.ip}] Успешное подключение ({auth_type}) по SSH на порту {self.active_port}")
            return True
        except Exception as e:
            logger.error(f"[{self.ip}] Ошибка авторизации ({auth_type}): {e}")
            return False

    def change_local_admin_password(self) -> bool:
        if not self.ssh_client:
            return False

        safe_pass = self._escape_mikrotik_string(self.new_admin_pass)
        cmd = f'/user set [find name="{self.target_admin_user}"] password="{safe_pass}"'

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd, timeout=10)
            err = stderr.read().decode("utf-8").strip()
            if err:
                logger.error(f"[{self.ip}] Ошибка смены пароля: {err}")
                return False
            logger.debug(f"[{self.ip}] Пароль для '{self.target_admin_user}' сменен.")
            return True
        except Exception as e:
            logger.error(f"[{self.ip}] Исключение при выполнении команды: {e}")
            return False

    def verify_new_admin_login(self) -> str:
        # Пауза перед подключением
        time.sleep(1.5)
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.ip,
                port=self.active_port,
                username=self.target_admin_user,
                password=self.new_admin_pass,
                timeout=10,
                look_for_keys=False,
                allow_agent=False,
            )
            ssh.close()
            logger.debug(f"[{self.ip}] Успешная верификация входа с новым паролем!")
            return "OK"
        except Exception as e:
            logger.error(f"[{self.ip}] Ошибка верификации нового пароля: {e}")
            return "FAIL"

    def close(self):
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception:
                pass
