import contextlib
from base64 import b64decode
from pathlib import Path
from typing import Any

import paramiko
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from models import ConnectionConfig

_KEY_CLASSES = (
    paramiko.Ed25519Key,
    paramiko.RSAKey,
    paramiko.ECDSAKey,
)

_HOST_KEY_CLASSES: dict[str, type[paramiko.PKey]] = {
    "ssh-ed25519": paramiko.Ed25519Key,
    "ssh-rsa": paramiko.RSAKey,
}
if hasattr(paramiko, "DSSKey"):
    _HOST_KEY_CLASSES["ssh-dss"] = paramiko.DSSKey


def _load_private_key(path: str, passphrase: str) -> paramiko.PKey:
    last_error: Exception | None = None
    for key_cls in _KEY_CLASSES:
        try:
            return key_cls.from_private_key_file(path, password=passphrase or None)
        except paramiko.SSHException as exc:
            last_error = exc
    raise last_error or paramiko.SSHException("Format de clé privée non reconnu")


def _fingerprint_hex(key: paramiko.PKey) -> str:
    return ":".join(f"{byte:02x}" for byte in key.get_fingerprint())


def _load_host_key(key_type: str, key_b64: str) -> paramiko.PKey:
    key_data = b64decode(key_b64.encode("ascii"), validate=True)
    if key_type.startswith("ecdsa-sha2-"):
        return paramiko.ECDSAKey(data=key_data)

    key_cls = _HOST_KEY_CLASSES.get(key_type)
    if key_cls is None:
        raise ValueError(f"Type de clé hôte SSH non supporté: {key_type}")
    return key_cls(data=key_data)


class _NotifyingRejectPolicy(paramiko.RejectPolicy):
    def __init__(self, on_unknown_host_key: Any) -> None:
        self._on_unknown_host_key = on_unknown_host_key

    def missing_host_key(
        self, client: paramiko.SSHClient, hostname: str, key: paramiko.PKey
    ) -> None:
        self._on_unknown_host_key.emit(
            hostname, key.get_name(), _fingerprint_hex(key), key.get_base64()
        )
        super().missing_host_key(client, hostname, key)


class SSHWorker(QObject):
    """Vit dans un QThread dédié ; toutes les opérations paramiko passent par ici."""

    connected = Signal()
    connection_error = Signal(str)
    data_received = Signal(str)
    disconnected = Signal()
    host_key_unknown = Signal(str, str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._client: paramiko.SSHClient | None = None
        self._channel: paramiko.Channel | None = None
        self._known_hosts_file = str(Path("~/.ssh/known_hosts").expanduser())
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(50)
        self._poll_timer.timeout.connect(self._poll_channel)

    @Slot(ConnectionConfig)
    def connect_to_host(self, config: ConnectionConfig) -> None:
        self._teardown()
        client: paramiko.SSHClient | None = None
        try:
            self._known_hosts_file = str(Path(config.known_hosts_file).expanduser())
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            with contextlib.suppress(FileNotFoundError):
                client.load_host_keys(self._known_hosts_file)
            client.set_missing_host_key_policy(
                _NotifyingRejectPolicy(self.host_key_unknown)
            )
            connect_kwargs = {
                "hostname": config.host,
                "port": config.port,
                "username": config.username,
                "timeout": config.timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }
            if config.auth_method == "password":
                connect_kwargs["password"] = config.password
            else:
                connect_kwargs["pkey"] = _load_private_key(
                    config.key_path, config.passphrase
                )

            client.connect(**connect_kwargs)
            channel = client.invoke_shell(term="xterm")
            channel.settimeout(0.0)

            self._client = client
            self._channel = channel
            self._poll_timer.start()
            self.connected.emit()
        except Exception as exc:  # paramiko/socket raise many distinct exception types
            if client is not None:
                with contextlib.suppress(Exception):
                    client.close()
            self.connection_error.emit(str(exc))

    @Slot()
    def _poll_channel(self) -> None:
        if self._channel is None:
            return
        try:
            if self._channel.recv_ready():
                data = self._channel.recv(4096).decode("utf-8", errors="replace")
                if data:
                    self.data_received.emit(data)
            if self._channel.closed:
                self._teardown()
                self.disconnected.emit()
        except Exception as exc:
            self.connection_error.emit(str(exc))
            self._teardown()
            self.disconnected.emit()

    @Slot(str)
    def send_text(self, text: str) -> None:
        if self._channel is None:
            return
        try:
            self._channel.send(text)
        except Exception as exc:
            self.connection_error.emit(str(exc))

    @Slot()
    def disconnect_from_host(self) -> None:
        was_connected = self._channel is not None
        self._teardown()
        if was_connected:
            self.disconnected.emit()

    @Slot(str, str, str)
    def accept_host_key(self, hostname: str, key_type: str, key_b64: str) -> None:
        try:
            known_hosts_path = Path(self._known_hosts_file).expanduser()
            known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
            host_keys = paramiko.HostKeys()
            if known_hosts_path.exists():
                host_keys.load(str(known_hosts_path))
            host_keys.add(hostname, key_type, _load_host_key(key_type, key_b64))
            host_keys.save(str(known_hosts_path))
        except Exception as exc:
            self.connection_error.emit(str(exc))

    def _teardown(self) -> None:
        self._poll_timer.stop()
        if self._channel is not None:
            with contextlib.suppress(Exception):
                self._channel.close()
            self._channel = None
        if self._client is not None:
            with contextlib.suppress(Exception):
                self._client.close()
            self._client = None
