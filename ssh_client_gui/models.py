from dataclasses import dataclass


@dataclass
class ConnectionConfig:
    host: str
    port: int
    username: str
    auth_method: str  # "password" or "key"
    password: str = ""
    key_path: str = ""
    passphrase: str = ""
    timeout: int = 10
    known_hosts_file: str = "~/.ssh/known_hosts"

    @property
    def label(self) -> str:
        return f"{self.username}@{self.host}:{self.port}"
