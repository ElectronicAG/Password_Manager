"""Rutas HTTP; conserva los endpoints utilizados por las plantillas actuales."""

import csv
import json
import secrets
from functools import wraps

from flask import (
    Flask, Response, current_app, flash, jsonify, redirect,
    render_template, request, session, url_for,
)

from .services import EntryNotFound, SEARCH_FIELDS, VaultService, generate_password


def login_required(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return decorated


def vault() -> VaultService:
    return current_app.extensions['vault']


def entry_form() -> dict:
    return {key: request.form.get(key, '') for key in ('name', 'link', 'email', 'password')}


def login():
    if session.get('authenticated'):
        return redirect(url_for('manager'))
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip().encode('utf-8')
        password = request.form.get('password', '').encode('utf-8')
        valid_name = secrets.compare_digest(name, current_app.config['ADMIN_NAME'].encode('utf-8'))
        valid_password = secrets.compare_digest(password, current_app.config['ADMIN_PASSWORD'].encode('utf-8'))
        if valid_name and valid_password:
            session.clear()
            session['authenticated'] = True
            return redirect(url_for('manager'))
        error = 'Credenciales incorrectas.'
    return render_template('login.html', error=error)


def logout():
    session.clear()
    return redirect(url_for('login'))


@login_required
def manager():
    query = request.args.get('q', '').strip().lower()
    field = request.args.get('field', 'all')
    if field not in SEARCH_FIELDS:
        field = 'all'
    entries = vault().search(query, field)
    return render_template('manager.html', entries=entries, q=query, field=field, total=len(entries))


@login_required
def add_entry():
    if request.method == 'POST':
        try:
            entry = vault().add(entry_form())
        except ValueError as exc:
            flash(str(exc), 'error')
            return redirect(url_for('add_entry'))
        flash(f"Entrada '{entry['name']}' agregada.", 'success')
        return redirect(url_for('manager'))
    return render_template('add.html')


@login_required
def edit_entry(entry_id: str):
    try:
        if request.method == 'POST':
            try:
                entry = vault().update(entry_id, entry_form())
            except ValueError as exc:
                flash(str(exc), 'error')
                return redirect(url_for('edit_entry', entry_id=entry_id))
            flash(f"Entrada '{entry['name']}' actualizada.", 'success')
            return redirect(url_for('manager'))
        entry = vault().get(entry_id)
    except EntryNotFound as exc:
        flash(str(exc), 'error')
        return redirect(url_for('manager'))
    entry['history_decrypted'] = entry.pop('history')
    return render_template('edit.html', entry=entry)


@login_required
def delete_entry(entry_id: str):
    try:
        vault().delete(entry_id)
    except EntryNotFound as exc:
        flash(str(exc), 'error')
    else:
        flash('Entrada eliminada.', 'success')
    return redirect(url_for('manager'))


@login_required
def api_generate():
    try:
        length = int(request.args.get('length', '16'))
    except ValueError:
        return jsonify(error='La longitud debe ser un número entero.'), 400
    password = generate_password(
        length,
        numbers=request.args.get('numbers', '1') == '1',
        upper=request.args.get('upper', '1') == '1',
        special=request.args.get('special', '1') == '1',
    )
    return jsonify(password=password)


@login_required
def export_csv():
    return Response(
        vault().export_csv(), mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=keyvault_export.csv'},
    )


@login_required
def import_csv():
    uploaded = request.files.get('csvfile')
    if not uploaded:
        flash('No se seleccionó archivo.', 'error')
        return redirect(url_for('manager'))
    try:
        added = vault().import_csv(uploaded.read())
    except (ValueError, csv.Error):
        flash('CSV inválido: revisa la codificación UTF-8 y las columnas name y password.', 'error')
    else:
        flash(f'{added} entrada(s) importadas correctamente.', 'success')
    return redirect(url_for('manager'))


@login_required
def export_json():
    return Response(
        json.dumps(vault().repository.load(), ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=keyvault_backup.json'},
    )


def register_routes(app: Flask) -> None:
    rules = (
        ('/', login, ['GET', 'POST']),
        ('/logout', logout, ['GET']),
        ('/manager', manager, ['GET']),
        ('/add', add_entry, ['GET', 'POST']),
        ('/edit/<entry_id>', edit_entry, ['GET', 'POST']),
        ('/delete/<entry_id>', delete_entry, ['POST']),
        ('/api/generate', api_generate, ['GET']),
        ('/export/csv', export_csv, ['GET']),
        ('/import/csv', import_csv, ['POST']),
        ('/export/json', export_json, ['GET']),
    )
    for rule, view, methods in rules:
        app.add_url_rule(rule, endpoint=view.__name__, view_func=view, methods=methods)
