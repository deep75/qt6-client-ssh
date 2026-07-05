# Copilot instructions for this repository

Quick commands
- Run the app (from repository root):
  - python ssh_client_gui/main.py
- Linting (ruff is configured in ssh_client_gui/ruff.toml):
  - ruff check ssh_client_gui || ruff check .

Tests
- No automated tests are present in the repository. If pytest is added, run a single test with:
  - pytest path/to/test_file.py::test_name

High-level architecture
- UI: QML files live in ssh_client_gui/qml (Main.qml loads QML components and the SshBridge QmlElement).
- Bridge: ssh_client_gui/bridge.py defines SshBridge (a QmlElement) that exposes properties, signals and slots to QML and manages an SSHWorker running in a dedicated QThread.
- Worker: ssh_client_gui/ssh_worker.py contains SSHWorker which performs all paramiko operations (connect, recv loop, send, teardown). All blocking/networking runs inside the worker thread; the bridge communicates by Qt Signals/Slots only.
- Models: ssh_client_gui/models.py defines ConnectionConfig (dataclass) used to pass connection parameters between UI and worker.

Key conventions and repository specifics
- QML <-> Python interop:
  - QML-visible methods and properties intentionally use camelCase (e.g., connectToHost, sendCommand, connected, outputText). bridge.py exposes these for QML.
  - The QML import name/version are declared in bridge.py (QML_IMPORT_NAME = "SshClient", QML_IMPORT_MAJOR_VERSION = 1); Main.qml imports `SshClient 1.0`.
- Threading model:
  - SSHWorker lives in a QThread; all paramiko usage must remain inside SSHWorker to avoid blocking the UI thread.
- Linting rules:
  - ruff.toml is present and includes per-file ignores for bridge.py because the QML API requires camelCase names (see lint.per-file-ignores). Respect those when adjusting names exposed to QML.
- Key-loading support:
  - ssh_worker.py contains a helper that tries Ed25519, RSA and ECDSA key classes in that order. Keep that ordering if changing key support.
- No packaging detected:
  - The ssh_client_gui directory is not a Python package (no __init__.py). Run the app via the script path rather than `python -m` unless you add package metadata.

AI / assistant configs found
- A minimal Claude config file exists at .claude (contains `settings.local.json`). No other AI assistant rule files (CLAUDE.md, AGENTS.md, .cursorrules, etc.) were found.

If you want changes
- Ask to include additional notes (e.g., dependency installation lines, or CI steps) or to incorporate any existing docs into this guidance.
