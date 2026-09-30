from flask import Flask

from .config import load_config
from .crypto import DecryptionError, PasswordCipher
from .routes import register_routes
from .services import VaultService
from .storage import JsonRepository, StorageError


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(load_config())
    if config is not None:
        app.config.update(config)

    app.extensions['vault'] = VaultService(
        JsonRepository(app.config['DATA_FILE']),
        PasswordCipher(app.config['NACL_KEY']),
    )
    register_routes(app)

    @app.errorhandler(StorageError)
    @app.errorhandler(DecryptionError)
    def handle_vault_error(error):
        app.logger.error('Error del gestor: %s', type(error).__name__)
        return (
            'No se pudo acceder a los datos. Revisa el archivo y la clave ADMIN_CODIGN.',
            500,
            {'Content-Type': 'text/plain; charset=utf-8'},
        )

    @app.after_request
    def prevent_sensitive_cache(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    return app


def main() -> None:
    """Punto de entrada ya declarado en pyproject.toml."""
    create_app().run(debug=False, host='127.0.0.1', port=5000)
