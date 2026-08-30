# 🔐 KeyVault - Password Manager

KeyVault is a local password manager built with Flask, NaCl encryption, and CSV import/export support.

## Installation

```bash
# 1. Install the dependencies
pip install -r requirements.txt

# 2. Configure the credentials
cp .env.example .env
# Edit .env and add your username, password, access code, and Flask secret.

# 3. Run the application
python app.py
# Open http://localhost:5000
```

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```dotenv
# KeyVault .env
# Copy this file as ".env" and complete the values.
# NEVER upload the real .env file to Git.

# Password manager access credentials
ADMIN_NAME=
ADMIN_PASSWORD=
ADMIN_CODIGN=

# Flask secret key
# Generate a random value with:
# python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET=
```

> Keep the variable name `ADMIN_CODIGN` unchanged if that is the exact name used by the application. Add `.env` to `.gitignore` and never commit real credentials or secret keys.

## Features

| Feature | Description |
| --- | --- |
| 🔐 Secure login | Authentication using the username and password stored in `.env` |
| 🔒 NaCl encryption | Passwords encrypted with PyNaCl SecretBox (XSalsa20-Poly1305) |
| ⌕ Real-time search | Instant filtering by name, email address, or URL |
| ⚙ Password generator | Adjustable length, uppercase letters, numbers, special characters, and a strength indicator |
| ✎ Entry editing | Update any stored field, including the password |
| ↓ CSV export | Download all decrypted entries as a CSV file |
| ↑ CSV import | Import entries from an external CSV file and encrypt them automatically |
| ⎘ Copy to clipboard | Copy an email address or password with one click |

## Security

- Passwords are encrypted with **NaCl SecretBox** (XSalsa20-Poly1305) before they are saved to the JSON file.
- The encryption key is derived from `ADMIN_PASSWORD` using SHA-256.
- If you change `ADMIN_PASSWORD` in `.env`, **you will no longer be able to decrypt previously stored entries**. Export them to CSV before changing it.
- The `Data_P.json` file never stores passwords in plain text.
- Add both `Data_P.json` and `.env` to `.gitignore`.
- CSV exports contain decrypted credentials. Store them securely and delete them when they are no longer needed.
- Use a long, unique value for `ADMIN_PASSWORD` and generate `FLASK_SECRET` with the command shown above.

Recommended `.gitignore` entries:

```gitignore
.env
Data_P.json
__pycache__/
*.pyc
```

## Project Structure

```text
passmanager/
├── app.py              # Flask backend
├── requirements.txt
├── .env.example        # Configuration template
├── .env                # Local configuration - DO NOT commit
├── Data_P.json         # Auto-generated encrypted database
├── static/
│   └── style.css       # Global styles
└── templates/
    ├── login.html
    ├── manager.html    # Main view with real-time search
    ├── add.html        # Add entry and generate a password
    └── edit.html       # Edit entry and generate a password
```

## Acknowledgments

This project was developed with assistance from **Claude Opus 4.7**.
