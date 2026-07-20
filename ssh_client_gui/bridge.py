from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot
from PySide6.QtQml import QmlElement

from models import ConnectionConfig
from ssh_worker import SSHWorker

QML_IMPORT_NAME = "SshClient"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class SshBridge(QObject):
    """Expose la connexion SSH à QML et pilote le SSHWorker dans son thread."""

    connect_requested = Signal(ConnectionConfig)
    send_text_requested = Signal(str)
    disconnect_requested = Signal()
    accept_host_key_requested = Signal(str, str, str)

    connectedChanged = Signal()
    statusChanged = Signal()
    outputTextChanged = Signal()
    pendingHostKeyBase64Changed = Signal()
    errorOccurred = Signal(str)
    host_key_unknown = Signal(str, str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._connected = False
        self._status = "Déconnecté"
        self._output_text = ""
        self._pending_host_key_base64 = ""

        self._thread = QThread(self)
        self._worker = SSHWorker()
        self._worker.moveToThread(self._thread)

        self.connect_requested.connect(self._worker.connect_to_host)
        self.send_text_requested.connect(self._worker.send_text)
        self.disconnect_requested.connect(self._worker.disconnect_from_host)
        self.accept_host_key_requested.connect(self._worker.accept_host_key)

        self._worker.connected.connect(self._on_connected)
        self._worker.connection_error.connect(self._on_connection_error)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.disconnected.connect(self._on_disconnected)
        self._worker.host_key_unknown.connect(self._on_host_key_unknown)

        self._thread.start()

    @Property(bool, notify=connectedChanged)
    def connected(self) -> bool:
        return self._connected

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=outputTextChanged)
    def outputText(self) -> str:
        return self._output_text

    @Property(str, notify=pendingHostKeyBase64Changed)
    def pendingHostKeyBase64(self) -> str:
        return self._pending_host_key_base64

    @Slot(str, int, str, str, str, str, str, int)
    def connectToHost(
        self,
        host: str,
        port: int,
        username: str,
        auth_method: str,
        password: str,
        key_path: str,
        passphrase: str,
        timeout: int,
    ) -> None:
        config = ConnectionConfig(
            host=host,
            port=port,
            username=username,
            auth_method=auth_method,
            password=password,
            key_path=key_path,
            passphrase=passphrase,
            timeout=timeout,
        )
        self._output_text = ""
        self.outputTextChanged.emit()
        self._set_status(f"Connexion à {config.label}…")
        self.connect_requested.emit(config)

    @Slot(str)
    def sendCommand(self, text: str) -> None:
        if not text:
            return
        self.send_text_requested.emit(text + "\n")

    @Slot()
    def disconnectFromHost(self) -> None:
        self.disconnect_requested.emit()

    @Slot(str, str, str)
    def acceptHostKey(self, hostname: str, key_type: str, key_b64: str) -> None:
        effective_key_b64 = key_b64 or self._pending_host_key_base64
        if not effective_key_b64:
            self.errorOccurred.emit("Aucune clé hôte en attente à accepter.")
            return
        self.accept_host_key_requested.emit(hostname, key_type, effective_key_b64)
        self._pending_host_key_base64 = ""
        self.pendingHostKeyBase64Changed.emit()

    @Slot()
    def clearOutput(self) -> None:
        self._output_text = ""
        self.outputTextChanged.emit()

    @Slot(QUrl, result=str)
    def toLocalPath(self, url: QUrl) -> str:
        return url.toLocalFile()

    @Slot()
    def shutdown(self) -> None:
        self.disconnect_requested.emit()
        self._thread.quit()
        self._thread.wait(2000)

    def _on_connected(self) -> None:
        self._connected = True
        self.connectedChanged.emit()
        self._set_status("Connecté")

    def _on_connection_error(self, message: str) -> None:
        self._connected = False
        self.connectedChanged.emit()
        self._set_status("Déconnecté")
        self.errorOccurred.emit(message)

    def _on_data_received(self, data: str) -> None:
        self._output_text += data
        self.outputTextChanged.emit()

    def _on_disconnected(self) -> None:
        self._connected = False
        self.connectedChanged.emit()
        self._set_status("Déconnecté")

    def _on_host_key_unknown(
        self, hostname: str, key_type: str, fingerprint: str, key_b64: str
    ) -> None:
        self._pending_host_key_base64 = key_b64
        self.pendingHostKeyBase64Changed.emit()
        self._set_status("Clé hôte inconnue")
        self.host_key_unknown.emit(hostname, key_type, fingerprint)

    def _set_status(self, status: str) -> None:
        self._status = status
        self.statusChanged.emit()
