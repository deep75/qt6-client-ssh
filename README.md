# qt6-client-ssh

A desktop SSH client built with **PySide6** (Qt 6 for Python), using **QML / Qt Quick** for the UI
and **paramiko** as the SSH backend.

## Features

- Connection form: host, port, username, timeout, password or private-key (Ed25519 / RSA / ECDSA)
  authentication with optional passphrase, key file picker
- Live output panel acting as a simple terminal (auto-scrolling), with a command input field
- Connection status indicator and error banner
- All SSH/network I/O runs on a dedicated `QThread`, keeping the UI responsive

## Architecture

```
ssh_client_gui/
  main.py               entry point: QGuiApplication + QQmlApplicationEngine
  bridge.py              SshBridge: QmlElement exposed to QML, owns the SSHWorker thread
  ssh_worker.py           SSHWorker: all paramiko calls (connect, recv loop, send, teardown)
  models.py               ConnectionConfig dataclass passed from the UI to the worker
  qml/
    Main.qml              application window, header/status bar, error banner
    ConnectionForm.qml     connection form (left panel)
    OutputPanel.qml        terminal output + command input (right panel)
  ruff.toml               Ruff config (camelCase names in bridge.py are QML API, not Python API)
  pysidedeploy.spec        pyside6-deploy/Nuitka packaging config (see Packaging below)
```

Data flow: QML calls a `@Slot` on `SshBridge` (e.g. `connectToHost(...)`) → `SshBridge` emits an
internal Qt signal → `SSHWorker`, living in its own `QThread`, does the blocking paramiko work →
emits signals back (`connected`, `data_received`, `connection_error`, `disconnected`) → `SshBridge`
updates its `Property` values (`connected`, `status`, `outputText`) → QML re-renders via bindings.

Qt handles the cross-thread signal delivery automatically (queued connections), so no manual
locking is needed.

## Requirements

- Python 3.10+
- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython-6/) 6.4+ (uses `QtQuick.Controls.Material`,
  `QmlElement`)
- [paramiko](https://www.paramiko.org/)
- [uv](https://docs.astral.sh/uv/) (recommended for managing the virtual environment)

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install PySide6 paramiko
```

## Running

```bash
python ssh_client_gui/main.py
```

Fill in the connection form on the left, choose password or private-key authentication, and click
**Se connecter**. Output appears in the terminal panel on the right; type a command and press Enter
(or click **Envoyer**) to run it.

### Known limitations

- Host key verification uses paramiko's `AutoAddPolicy` (new host keys are trusted automatically).
  Harden this to `RejectPolicy` + a known_hosts file if you need strict verification.
- The output panel is a plain text sink, not a full ANSI terminal emulator — escape sequences from
  the remote shell (colors, cursor movement) are shown as-is rather than interpreted.

## Development

Static analysis is run with [Ruff](https://docs.astral.sh/ruff/) and
[ty](https://docs.astral.sh/ty/):

```bash
uv pip install ruff ty
ruff check ssh_client_gui/
ty check ssh_client_gui/
```

`ssh_client_gui/ruff.toml` ignores `N802`/`N815` (camelCase naming) specifically in `bridge.py`,
since those names are the Qt/QML API surface, not Python API.

## Packaging (Linux)

Qt/PySide6 ships an official deployment tool, **`pyside6-deploy`**, which uses
[Nuitka](https://nuitka.net/) to compile the app and PySide6 into a standalone native executable —
end users don't need Python or Qt installed. It targets Windows (`.exe`), Linux (`.bin`) and macOS
(`.app`), but each target must be built **on that OS** (no cross-compilation).

System prerequisites on Debian/Ubuntu:

```bash
sudo apt install patchelf gcc
```

Build:

```bash
uv pip install nuitka patchelf
cd ssh_client_gui
pyside6-deploy -c pysidedeploy.spec -f
```

This produces a standalone folder at `ssh_client_gui/deployment/main.dist/`, with the executable at
`main.dist/ssh_client_gui.bin` (or a single binary if you switch `mode` to `onefile` in
`pysidedeploy.spec`).

Notes on `pysidedeploy.spec`:
- `python_path` defaults to `python3` — point it at your venv's interpreter
  (e.g. `.venv/bin/python3`) if it's not the one on your `PATH`.
- `extra_args` includes `--static-libpython=no`: many Linux Python builds (Anaconda/conda-forge,
  or Debian/Ubuntu without `python3-dev`) don't ship a usable static `libpython`, which makes
  Nuitka fail with "Automatic detection of static libpython failed". Disabling it links against
  the shared `libpython` instead and works everywhere.
- To ship for multiple platforms from one repository, run `pyside6-deploy` in a CI matrix
  (e.g. GitHub Actions with `windows-latest` / `ubuntu-latest` / `macos-latest` runners) rather
  than trying to cross-compile from a single machine.

Qt also provides the **Qt Installer Framework (QtIFW)** for wrapping the resulting binary in a
proper platform installer, and `pyside6-android-deploy` for Android packaging.
