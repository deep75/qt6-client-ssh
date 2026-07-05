import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from bridge import SshBridge


def main() -> int:
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    qml_file = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(str(qml_file))

    root_objects = engine.rootObjects()
    if not root_objects:
        return -1

    # PySide6's stub types the @QmlElement decorator as `(object) -> object`,
    # so ty loses the concrete class here even though findChild works fine at runtime.
    bridge = root_objects[0].findChild(SshBridge)  # ty: ignore[invalid-argument-type]
    if bridge is not None:
        app.aboutToQuit.connect(bridge.shutdown)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
