"""Operaciones del gestor independientes de Flask y de las plantillas."""

import csv
import io
import secrets
import string

from .crypto import PasswordCipher
from .storage import JsonRepository, next_id

SEARCH_FIELDS = ('name', 'email', 'link', 'password')
CSV_FIELDS = ('id', 'name', 'link', 'email', 'password')


class EntryNotFound(LookupError):
    """No existe una entrada con el identificador solicitado."""


class VaultService:
    def __init__(self, repository: JsonRepository, cipher: PasswordCipher) -> None:
        self.repository = repository
        self.cipher = cipher

    @staticmethod
    def _find(entries: list[dict], entry_id: str) -> dict:
        for entry in entries:
            if str(entry['id']) == str(entry_id):
                return entry
        raise EntryNotFound('Entrada no encontrada.')

    @staticmethod
    def _fields(values) -> dict:
        fields = {key: (values.get(key) or '').strip() for key in ('name', 'link', 'email')}
        fields['name'] = fields['name'].upper()
        # Los espacios pueden formar parte de una contraseña válida.
        fields['password'] = values.get('password') or ''
        if not fields['name'] or not fields['password']:
            raise ValueError('Nombre y contraseña son obligatorios.')
        return fields

    def _display(self, entry: dict) -> dict:
        result = dict(entry)
        result['password'] = self.cipher.decrypt(entry['password']) if entry.get('password') else ''
        result['history'] = [self.cipher.decrypt(p) for p in (entry.get('history') or []) if p]
        return result

    def search(self, query: str = '', field: str = 'all') -> list[dict]:
        fields = SEARCH_FIELDS if field not in SEARCH_FIELDS else (field,)
        query = query.strip().lower()
        entries = [self._display(e) for e in self.repository.load()]
        return [e for e in entries if any(query in e.get(f, '').lower() for f in fields)]

    def get(self, entry_id: str) -> dict:
        return self._display(self._find(self.repository.load(), entry_id))

    def _new_entry(self, entries: list[dict], fields: dict) -> dict:
        return {
            **fields, 'id': next_id(entries),
            'password': self.cipher.encrypt(fields['password']), 'history': [],
        }

    def add(self, values) -> dict:
        fields = self._fields(values)
        with self.repository.transaction() as entries:
            entry = self._new_entry(entries, fields)
            entries.append(entry)
        return entry

    def update(self, entry_id: str, values) -> dict:
        fields = self._fields(values)
        with self.repository.transaction() as entries:
            entry = self._find(entries, entry_id)
            previous = entry.get('password', '')
            if not previous or self.cipher.decrypt(previous) != fields['password']:
                history = list(entry.get('history') or [])
                if previous:
                    history.insert(0, previous)
                entry['history'] = history[:2]
                entry['password'] = self.cipher.encrypt(fields['password'])
            for field in ('name', 'link', 'email'):
                entry[field] = fields[field]
        return entry

    def delete(self, entry_id: str) -> None:
        with self.repository.transaction() as entries:
            entries.remove(self._find(entries, entry_id))

    def export_csv(self) -> str:
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for entry in self.repository.load():
            row = {key: entry.get(key, '') for key in CSV_FIELDS}
            row['password'] = self.cipher.decrypt(row['password']) if row['password'] else ''
            writer.writerow(row)
        return output.getvalue()

    def import_csv(self, content: bytes) -> int:
        reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''), strict=True)
        if not reader.fieldnames:
            raise ValueError('El archivo CSV está vacío.')
        headers = {h.strip().lower() for h in reader.fieldnames}
        if not {'name', 'password'} <= headers:
            raise ValueError('El CSV debe incluir name y password.')
        added = 0
        with self.repository.transaction() as entries:
            for row in reader:
                if None in row:
                    raise ValueError('El CSV contiene una fila con columnas adicionales.')
                values = {key.strip().lower(): value or '' for key, value in row.items()}
                if not values.get('name', '').strip() or not values.get('password'):
                    continue
                entries.append(self._new_entry(entries, self._fields(values)))
                added += 1
        return added


def generate_password(length: int = 16, *, numbers: bool = True,
                      upper: bool = True, special: bool = True) -> str:
    length = max(4, min(128, length))
    groups = [string.ascii_lowercase]
    if numbers:
        groups.append(string.digits)
    if upper:
        groups.append(string.ascii_uppercase)
    if special:
        groups.append(string.punctuation)
    characters = ''.join(groups)
    password = [secrets.choice(group) for group in groups]
    password.extend(secrets.choice(characters) for _ in range(length - len(password)))
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)
