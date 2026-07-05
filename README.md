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
  pyproject.toml           project metadata and dependencies (managed by uv)
  uv.lock                  locked dependency versions
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

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended for managing the virtual environment and dependencies)
- [Qt for Python (PySide6)](https://doc.qt.io/qtforpython-6/) 6.6+ (installed automatically via `uv sync`)
- [paramiko](https://www.paramiko.org/) (installed automatically via `uv sync`)

## Installation

From the repository root:

```bash
cd ssh_client_gui
uv sync
```

This creates a virtual environment, installs locked dependencies from `uv.lock`, and registers the
`ssh-client-gui` console script.

## Running

```bash
cd ssh_client_gui
uv run ssh-client-gui
```

Alternatively:

```bash
uv run python main.py
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
ruff check .
ty check .
```

`ruff.toml` ignores `N802`/`N815` (camelCase naming) specifically in `bridge.py`, since those
names are the Qt/QML API surface, not Python API.

## Packaging

There are two distinct packaging paths. **uv does not compile a native Qt binary on its own** — it
manages the Python environment and can build a wheel; a standalone executable requires
**`pyside6-deploy`** (bundled with PySide6) and **Nuitka**.

### Python wheel (`uv build`)

Produces a `.whl` installable with pip. End users still need Python and the runtime dependencies.

```bash
cd ssh_client_gui
uv build
```

Output: `dist/ssh_client_gui-0.1.0-py3-none-any.whl`

### Native executable (`pyside6-deploy` + Nuitka)

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
cd ssh_client_gui
uv sync
uv pip install nuitka patchelf
.venv/bin/pyside6-deploy -c pysidedeploy.spec -f
```

This produces a standalone folder at `deployment/main.dist/`, with the executable at
`main.dist/ssh_client_gui.bin` (or a single binary if you switch `mode` to `onefile` in
`pysidedeploy.spec`).

Notes on `pysidedeploy.spec`:

- Set `python_path` to your venv interpreter (e.g. `.venv/bin/python3`) so Nuitka uses the same
  Python and packages as `uv sync`.
- `extra_args` includes `--static-libpython=no`: many Linux Python builds (Anaconda/conda-forge,
  or Debian/Ubuntu without `python3-dev`) don't ship a usable static `libpython`, which makes
  Nuitka fail with "Automatic detection of static libpython failed". Disabling it links against
  the shared `libpython` instead and works everywhere.
- To ship for multiple platforms from one repository, run `pyside6-deploy` in a CI matrix
  (e.g. GitHub Actions with `windows-latest` / `ubuntu-latest` / `macos-latest` runners) rather
  than trying to cross-compile from a single machine.

Qt also provides the **Qt Installer Framework (QtIFW)** for wrapping the resulting binary in a
proper platform installer, and `pyside6-android-deploy` for Android packaging.
