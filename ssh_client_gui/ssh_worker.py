import contextlib

import paramiko
from PySide6.QtCore import QObject, QTimer, Signal, Slot

from models import ConnectionConfig

_KEY_CLASSES = (
    paramiko.Ed25519Key,
    paramiko.RSAKey,
    paramiko.ECDSAKey,
)


def _load_private_key(path: str, passphrase: str) -> paramiko.PKey:
    last_error: Exception | None = None
    for key_cls in _KEY_CLASSES:
        try:
            return key_cls.from_private_key_file(path, password=passphrase or None)
        except paramiko.SSHException as exc:
            last_error = exc
    raise last_error or paramiko.SSHException("Format de clé privée non reconnu")


class SSHWorker(QObject):
    """Vit dans un QThread dédié ; toutes les opérations paramiko passent par ici."""

    connected = Signal()
    connection_error = Signal(str)
    data_received = Signal(str)
    disconnected = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._client: paramiko.SSHClient | None = None
        self._channel: paramiko.Channel | None = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(50)
        self._poll_timer.timeout.connect(self._poll_channel)

    @Slot(ConnectionConfig)
    def connect_to_host(self, config: ConnectionConfig) -> None:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
