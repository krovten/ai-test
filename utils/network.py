import socket
import subprocess

def ping_host(ip: str, timeout: int = 1) -> bool:
    cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def check_port(ip: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, OSError):
        return False
