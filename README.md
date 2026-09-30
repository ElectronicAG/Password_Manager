# Password Manager with uv (Astral)

This guide explains how to run the reorganized project using the Python files provided. Keep the original project's `pyproject.toml`, `uv.lock`, templates, and styles. You can save this guide as `README.md` in the project root.

## 1. Install uv

**Windows, in PowerShell:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux or macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Reopen your terminal and verify the installation:

```bash
uv --version
```

Reference: [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## 2. Place the files

Copy the eight provided `.py` files into `src/password_manager/`, replacing older files with the same names. All eight files must be together in that package.

| Path relative to the project root | Purpose |
| --- | --- |
| `pyproject.toml` | Dependencies, Python version requirement, and startup command |
| `uv.lock` | Resolved dependency versions |
| `README.md` | Project documentation |
| `src/password_manager/__init__.py` | Creates the application with `create_app()` and defines `main()` |
| `src/password_manager/__main__.py` | Allows running the package with `python -m` |
| `src/password_manager/password_manager.py` | Exposes the WSGI application as `app` |
| `src/password_manager/config.py` | Loads configuration |
| `src/password_manager/crypto.py` | Encrypts and decrypts passwords |
| `src/password_manager/storage.py` | Reads and saves JSON records |
| `src/password_manager/services.py` | Handles entries, history, searches, and CSV operations |
| `src/password_manager/routes.py` | Defines web routes |
| `src/password_manager/templates/` | Keep `login.html`, `manager.html`, `add.html`, and `edit.html` |
| `src/password_manager/static/style.css` | Keep the original styles |
| `src/password_manager/.env` | Local credentials and secret keys |
| `src/password_manager/Data_P.json` | Data file; created when data is first saved |

Filenames must match exactly: if a downloaded file is named `__init__(1).py`, rename it to `__init__.py`.

## 3. Install Python and dependencies

Open a terminal in the folder containing `pyproject.toml`. For example, if you are in its parent folder:

```bash
cd password_manager
```

The original project requires Python **3.14 or later**. To use 3.14:

```bash
uv python install 3.14
uv python pin 3.14
uv sync
```

`uv sync` prepares the `.venv` environment and installs the project and its declared dependencies: Flask, PyNaCl, and python-dotenv. You do not need to activate the environment manually when using `uv run`.

Your `pyproject.toml` already includes the startup command:

```toml
[project.scripts]
password-manager = "password_manager:main"
```

This tells `password-manager` to execute the `main()` function from the `password_manager` package, defined in `__init__.py`.

References: [installing Python](https://docs.astral.sh/uv/guides/install-python/) and [syncing the environment](https://docs.astral.sh/uv/concepts/projects/sync/).

## 4. Configure the .env file

If you already have a `.env` file, keep its values and make sure it is located at:

```text
src/password_manager/.env
```

For a new installation, create this file using the following structure and replace the example values:

```dotenv
ADMIN_NAME=your_username
ADMIN_PASSWORD="REPLACE_WITH_YOUR_PASSWORD"
ADMIN_CODIGN="REPLACE_WITH_A_RANDOM_SECRET"
FLASK_SECRET="REPLACE_WITH_ANOTHER_RANDOM_SECRET"
```

| Variable | Purpose |
| --- | --- |
| `ADMIN_NAME` | Username for signing in |
| `ADMIN_PASSWORD` | Password for signing in |
| `ADMIN_CODIGN` | Secret used to derive the data encryption key |
| `FLASK_SECRET` | Key used to sign session cookies |
| `DATA_FILE` | Optional path for storing the JSON file elsewhere |

The name `ADMIN_CODIGN` is kept exactly as written for compatibility with your previous code.

To generate a secret, run:

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

For a new installation, run this twice and use a different result for `ADMIN_CODIGN` and `FLASK_SECRET`.

**If you have already saved passwords, keep the previous value of `ADMIN_CODIGN`.** Changing it does not re-encrypt existing records and will prevent the application from decrypting them. Changing `ADMIN_PASSWORD` changes the login password but does not change the encryption key.

If you omit `DATA_FILE`, the application uses `src/password_manager/Data_P.json`. For another location, an absolute path is preferable. A relative path is resolved from the directory where you start the process.

Variables already defined in the environment take priority over the `.env` file. Restart the application after changing the configuration.

## 5. Run the application

From the project root:

```bash
uv run password-manager
```

You can also start the package with:

```bash
uv run python -m password_manager
```

Open this address in your browser:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

Sign in using your `ADMIN_NAME` and `ADMIN_PASSWORD` values. To stop the server, press **Ctrl+C** in the terminal.

For subsequent launches, just use `uv run password-manager`: uv checks the environment before running the command.

Reference: [running commands with uv](https://docs.astral.sh/uv/concepts/projects/run/).

## 6. Why imports use a dot

In this code:

```python
from . import create_app
```

The dot means “from the current package.” It imports `create_app` from the `password_manager` package's `__init__.py` file.

This example imports from a module within the same package:

```python
from .config import load_config
```

Running `uv run python -m password_manager` allows Python to recognize the package context. Running the internal file directly with `python src/password_manager/password_manager.py` can cause a relative import error.

## 7. Use the password manager

- **Add:** save a name, link, email address, and password.
- **Search:** filter by name, email address, link, or password.
- **Edit:** update fields and retain up to two previous passwords when the password changes.
- **Generate:** create a password using the selected options.
- **Export CSV:** download credentials with passwords in plain text.
- **Import CSV:** requires `name` and `password` columns; also supports `link` and `email`. Rows without a name or password are skipped.
- **Export JSON:** download records with encrypted passwords and password history; names, email addresses, and links remain readable.

To restore a JSON backup, stop the application, keep a copy of the current data file, and place the backup at the `DATA_FILE` path. You must use the same `ADMIN_CODIGN` value that was used to encrypt the backup. The interface does not include JSON import.

## 8. Troubleshooting

| Problem | What to check |
| --- | --- |
| `uv` is not recognized | Reopen the terminal and check that the installation added uv to your `PATH`. |
| `pyproject.toml` cannot be found | Change to the project root directory. |
| Incompatible Python version | Run `uv python install 3.14`, `uv python pin 3.14`, and `uv sync`. |
| `password-manager` cannot be found | Check `[project.scripts]` and run `uv sync`. |
| `attempted relative import with no known parent package` | Use `uv run password-manager` or `uv run python -m password_manager`. |
| `TemplateNotFound` | Make sure `templates/` is next to `__init__.py` and contains the original HTML files. |
| Incorrect credentials | Check the package's `.env` file and any environment variables that might override it. |
| Data could not be accessed | Check the JSON file, its permissions, and the original `ADMIN_CODIGN` value; preserve a copy of the file before changing it. |
| Port 5000 is already in use | Stop the other instance, or run `uv run flask --app password_manager:create_app run --port 5001` and open port 5001 in your browser. |

## Scope of this version

The main command starts Flask's local server on `127.0.0.1`, with debugging disabled. The JSON repository coordinates operations within one application instance; multiple processes require a different persistence mechanism.

Syntax and storage operations were checked when preparing the code. The full application was not run in the delivery environment because its dependencies were unavailable. After installing with uv, verify login and entry operations using a test entry before using real data.
