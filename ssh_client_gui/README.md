# ssh-client-gui

Client SSH graphique construit avec PySide6 et QML.

## Prérequis

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (recommandé pour gérer l'environnement virtuel)

## Installation

```bash
uv sync
```

## Lancement

```bash
uv run python main.py
```

## Qualité de code

Le projet utilise les outils de la suite Astral pour garantir la qualité du code Python.

### Linter et formateur : Ruff

[Ruff](https://docs.astral.sh/ruff/) assure le linting et le formatage du code.

Vérifier le style et détecter les erreurs :

```bash
ruff check .
```

Proposer les corrections automatiques :

```bash
ruff check . --fix
```

Vérifier le formatage :

```bash
ruff format --check .
```

Appliquer le formatage :

```bash
ruff format .
```

La configuration de Ruff se trouve dans [`ruff.toml`](ruff.toml).

### Vérification des types : ty

[ty](https://docs.astral.sh/ty/) est le vérificateur de types d'Astral.

Lancer l'analyse des types :

```bash
uv run --with ty ty check
```

> **Note :** `ty` n'est pas encore listé comme dépendance de développement dans [`pyproject.toml`](pyproject.toml). Il est invoqué temporairement via `uv run --with ty`.
