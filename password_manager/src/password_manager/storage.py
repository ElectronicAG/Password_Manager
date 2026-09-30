"""Persistencia JSON con escrituras atómicas y validación de registros."""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from threading import RLock


class StorageError(RuntimeError):
    """No fue posible leer o guardar el archivo de datos."""


class JsonRepository:
    """Serializa operaciones dentro de una instancia de la aplicación.

    Para varios procesos o servidores, sustituir por una base de datos
    transaccional. El bloqueo de este repositorio es local al proceso.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = RLock()

    def load(self) -> list[dict]:
        with self._lock:
            try:
                with self.path.open(encoding='utf-8') as source:
                    entries = json.load(source)
            except FileNotFoundError:
                return []
            except (OSError, ValueError) as exc:
                raise StorageError('No se pudo leer el archivo de datos.') from exc
            self._validate(entries)
            return entries

    @staticmethod
    def _validate(entries: list[dict]) -> None:
        if not isinstance(entries, list):
            raise StorageError('El archivo debe contener una lista de entradas.')
        ids = set()
        for entry in entries:
            if not isinstance(entry, dict) or 'id' not in entry:
                raise StorageError('Hay una entrada inválida en el archivo.')
            entry_id = str(entry['id'])
            if entry_id in ids:
                raise StorageError('Hay identificadores duplicados en el archivo.')
            ids.add(entry_id)
            for field in ('name', 'link', 'email', 'password'):
                if not isinstance(entry.get(field, ''), str):
                    raise StorageError('Hay un campo inválido en el archivo.')
            history = entry.get('history') or []
            if not isinstance(history, list) or not all(isinstance(p, str) for p in history):
                raise StorageError('El historial de contraseñas es inválido.')

    def save(self, entries: list[dict]) -> None:
        self._validate(entries)
        with self._lock:
            temporary = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    mode='w', encoding='utf-8', dir=self.path.parent,
                    prefix=f'.{self.path.name}.', delete=False,
                ) as target:
                    temporary = Path(target.name)
                    json.dump(entries, target, ensure_ascii=False, indent=2)
                    target.flush()
                    os.fsync(target.fileno())
                os.replace(temporary, self.path)
            except OSError as exc:
                raise StorageError('No se pudo guardar el archivo de datos.') from exc
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)

    @contextmanager
    def transaction(self):
        """Guarda solamente si la operación termina sin errores."""
        with self._lock:
            entries = self.load()
            yield entries
            self.save(entries)


def next_id(entries: list[dict]) -> str:
    ids = [int(e['id']) for e in entries if str(e.get('id', '')).isdecimal()]
    return str(max(ids, default=0) + 1)
