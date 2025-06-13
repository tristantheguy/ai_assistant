
import os
import platform
import psutil

class AIAgent:
    def __init__(self):
        self.name = "System Assistant"

    def gather_system_info(self):
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "cpu": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": {part.device: psutil.disk_usage(part.mountpoint)._asdict() for part in psutil.disk_partitions()},
            "network": psutil.net_if_addrs(),
            "users": [user._asdict() for user in psutil.users()],
            "boot_time": psutil.boot_time()
        }

    def list_files(self, directory="."):
        try:
            return os.listdir(directory)
        except Exception as e:
            return {"error": str(e)}

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path, content):
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
            return {"status": "success", "path": path}
        except Exception as e:
            return {"error": str(e)}
