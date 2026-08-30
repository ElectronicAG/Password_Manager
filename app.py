import os
import io
import csv
import json
import base64
import hashlib
import secrets
import string
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, Response)
from dotenv import load_dotenv
from nacl.secret import SecretBox
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(32))

# ── Auth config from .env ─────────────────────────────────────────────────────
ADMIN_NAME     = os.environ.get("ADMIN_NAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
ADMIN_CODIGN = os.environ.get("ADMIN_CODIGN", "changeme")

# ── NaCl encryption key derived from ADMIN_PASSWORD (SHA-256, 32 bytes) ──────
NACL_KEY = hashlib.sha256(ADMIN_CODIGN.encode()).digest()

def encrypt(plaintext: str) -> str:
    return base64.b64encode(SecretBox(NACL_KEY).encrypt(plaintext.encode())).decode()

def decrypt(ciphertext: str) -> str:
    try:
        return SecretBox(NACL_KEY).decrypt(base64.b64decode(ciphertext.encode())).decode()
    except Exception:
        return "⚠ decrypt error"

# ── JSON data file ────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "Data_P.json")

# Entry schema:
# {
#   "id":       "1",
#   "name":     "GITHUB",
#   "link":     "https://github.com",
#   "email":    "user@example.com",
#   "password": "<nacl-base64>",
#   "history":  ["<nacl-base64>", "<nacl-base64>"]   # max 2, newest first
# }

def load_entries() -> list:
    if not os.path.exists(DATA_FILE):
        _write_json([])
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_entries(entries: list) -> None:
    _write_json(entries)

def _write_json(data) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_id(entries: list) -> str:
    if not entries:
        return "1"
    ids = [int(e["id"]) for e in entries if str(e.get("id","")).isdigit()]
    return str(max(ids) + 1) if ids else "1"

def rotate_history(entry: dict, new_encrypted_pw: str) -> list:
    old_pw  = entry.get("password", "")
    history = list(entry.get("history") or [])
    if old_pw and old_pw != new_encrypted_pw:
        history.insert(0, old_pw)
        history = history[:2]
    return history

def _display(entry: dict) -> dict:
    d = dict(entry)
    d["password"] = decrypt(entry["password"]) if entry.get("password") else ""
    d["history"]  = [decrypt(h) for h in (entry.get("history") or []) if h]
    return d

# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("manager"))
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pw   = request.form.get("password", "").strip()
        if name == ADMIN_NAME and pw == ADMIN_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("manager"))
        error = "Credenciales incorrectas."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/manager")
@login_required
def manager():
    q     = request.args.get("q", "").strip().lower()
    field = request.args.get("field", "all")
    entries = load_entries()
    display = [_display(e) for e in entries]
    if q:
        def matches(d):
            if field == "all":
                haystack = [d.get("name",""), d.get("email",""),
                            d.get("link",""), d.get("password","")]
            else:
                haystack = [d.get(field, "")]
            return any(q in t.lower() for t in haystack)
        display = [d for d in display if matches(d)]
    return render_template("manager.html", entries=display,
                           q=q, field=field, total=len(display))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_entry():
    if request.method == "POST":
        name  = request.form.get("name", "").strip().upper()
        link  = request.form.get("link", "").strip()
        email = request.form.get("email", "").strip()
        pw    = request.form.get("password", "").strip()
        if not name or not pw:
            flash("Nombre y contraseña son obligatorios.", "error")
            return redirect(url_for("add_entry"))
        entries = load_entries()
        entries.append({
            "id":       next_id(entries),
            "name":     name,
            "link":     link,
            "email":    email,
            "password": encrypt(pw),
            "history":  [],
        })
        save_entries(entries)
        flash(f"Entrada '{name}' agregada.", "success")
        return redirect(url_for("manager"))
    return render_template("add.html")

@app.route("/edit/<entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entries = load_entries()
    entry   = next((e for e in entries if str(e.get("id")) == str(entry_id)), None)
    if not entry:
        flash("Entrada no encontrada.", "error")
        return redirect(url_for("manager"))
    if request.method == "POST":
        name  = request.form.get("name", "").strip().upper()
        link  = request.form.get("link", "").strip()
        email = request.form.get("email", "").strip()
        pw    = request.form.get("password", "").strip()
        if not name or not pw:
            flash("Nombre y contraseña son obligatorios.", "error")
            return redirect(url_for("edit_entry", entry_id=entry_id))
        for e in entries:
            if str(e.get("id")) == str(entry_id):
                new_enc     = encrypt(pw)
                e["history"]  = rotate_history(e, new_enc)
                e["name"]     = name
                e["link"]     = link
                e["email"]    = email
                e["password"] = new_enc
                break
        save_entries(entries)
        flash(f"Entrada '{name}' actualizada.", "success")
        return redirect(url_for("manager"))
    # GET: send decrypted copy
    d = _display(entry)
    d["id"] = entry["id"]
    d["history_decrypted"] = d.pop("history")
    return render_template("edit.html", entry=d)

@app.route("/delete/<entry_id>", methods=["POST"])
@login_required
def delete_entry(entry_id):
    entries = [e for e in load_entries() if str(e.get("id")) != str(entry_id)]
    save_entries(entries)
    flash("Entrada eliminada.", "success")
    return redirect(url_for("manager"))

# ── Password generator (AJAX) ─────────────────────────────────────────────────
@app.route("/api/generate")
@login_required
def api_generate():
    length  = max(4, min(128, int(request.args.get("length", 16))))
    numbers = request.args.get("numbers", "1") == "1"
    upper   = request.args.get("upper",   "1") == "1"
    special = request.args.get("special", "1") == "1"
    chars   = string.ascii_lowercase
    if numbers: chars += string.digits
    if upper:   chars += string.ascii_uppercase
    if special: chars += string.punctuation
    return jsonify({"password": "".join(secrets.choice(chars) for _ in range(length))})

# ── CSV export (passwords decrypted) ─────────────────────────────────────────
@app.route("/export/csv")
@login_required
def export_csv():
    entries = load_entries()
    out = io.StringIO()
    w   = csv.DictWriter(out, fieldnames=["id","name","link","email","password"])
    w.writeheader()
    for e in entries:
        w.writerow({
            "id":       e.get("id",""),
            "name":     e.get("name",""),
            "link":     e.get("link",""),
            "email":    e.get("email",""),
            "password": decrypt(e["password"]) if e.get("password") else "",
        })
    out.seek(0)
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=keyvault_export.csv"})

# ── CSV import ────────────────────────────────────────────────────────────────
@app.route("/import/csv", methods=["POST"])
@login_required
def import_csv():
    file = request.files.get("csvfile")
    if not file:
        flash("No se seleccionó archivo.", "error")
        return redirect(url_for("manager"))
    try:
        reader  = csv.DictReader(io.StringIO(file.read().decode("utf-8")))
        entries = load_entries()
        added   = 0
        for row in reader:
            # Accept both lowercase and capitalized field names
            name = (row.get("name") or row.get("Name","")).strip().upper()
            pw   = (row.get("password") or row.get("Password","")).strip()
            if not name or not pw:
                continue
            entries.append({
                "id":       next_id(entries),
                "name":     name,
                "link":     (row.get("link") or row.get("Link","")).strip(),
                "email":    (row.get("email") or row.get("Email","")).strip(),
                "password": encrypt(pw),
                "history":  [],
            })
            added += 1
        save_entries(entries)
        flash(f"{added} entrada(s) importadas correctamente.", "success")
    except Exception as ex:
        flash(f"Error al importar: {ex}", "error")
    return redirect(url_for("manager"))

# ── JSON backup export (encrypted, for safe backups) ─────────────────────────
@app.route("/export/json")
@login_required
def export_json():
    return Response(
        json.dumps(load_entries(), ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=keyvault_backup.json"},
    )

if __name__ == "__main__":
    load_entries()
    app.run(debug=False, host="127.0.0.1", port=5000)
