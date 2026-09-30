# Password Manager con uv (Astral)

Guía para ejecutar la versión reorganizada del proyecto usando los archivos Python entregados. Conserva el `pyproject.toml`, `uv.lock`, las plantillas y los estilos del proyecto original. Puedes guardar esta guía como `README.md` en la raíz del proyecto.

## 1. Instalar uv

**Windows, en PowerShell:**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux o macOS:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Abre de nuevo la terminal y comprueba la instalación:

```bash
uv --version
```

Referencia: [instalación oficial de uv](https://docs.astral.sh/uv/getting-started/installation/).

## 2. Colocar los archivos

Copia los ocho `.py` entregados dentro de `src/password_manager/`, reemplazando las versiones anteriores que tengan el mismo nombre. Todos deben estar juntos en ese paquete.

| Ruta desde la raíz del proyecto | Función |
| --- | --- |
| `pyproject.toml` | Dependencias, versión de Python y comando de inicio |
| `uv.lock` | Versiones resueltas de las dependencias |
| `README.md` | Documentación del proyecto |
| `src/password_manager/__init__.py` | Crea la aplicación con `create_app()` y define `main()` |
| `src/password_manager/__main__.py` | Permite ejecutar el paquete con `python -m` |
| `src/password_manager/password_manager.py` | Expone la aplicación WSGI como `app` |
| `src/password_manager/config.py` | Carga la configuración |
| `src/password_manager/crypto.py` | Cifra y descifra contraseñas |
| `src/password_manager/storage.py` | Lee y guarda los registros JSON |
| `src/password_manager/services.py` | Gestiona entradas, historial, búsquedas y CSV |
| `src/password_manager/routes.py` | Define las rutas web |
| `src/password_manager/templates/` | Conserva `login.html`, `manager.html`, `add.html` y `edit.html` |
| `src/password_manager/static/style.css` | Conserva los estilos originales |
| `src/password_manager/.env` | Credenciales y claves locales |
| `src/password_manager/Data_P.json` | Datos; se crea al guardar por primera vez |

Los nombres deben ser exactos: si una descarga se llama `__init__(1).py`, renómbrala a `__init__.py`.

## 3. Instalar Python y las dependencias

Abre la terminal en la carpeta que contiene `pyproject.toml`. Por ejemplo, si estás en su carpeta superior:

```bash
cd password_manager
```

El proyecto original requiere Python **3.14 o superior**. Para utilizar 3.14:

```bash
uv python install 3.14
uv python pin 3.14
uv sync
```

`uv sync` prepara el entorno `.venv` e instala el proyecto y sus dependencias declaradas: Flask, PyNaCl y python-dotenv. No necesitas activar el entorno manualmente al utilizar `uv run`.

Tu `pyproject.toml` ya incluye el comando de inicio:

```toml
[project.scripts]
password-manager = "password_manager:main"
```

Esto indica que `password-manager` ejecuta la función `main()` del paquete `password_manager`, definida en `__init__.py`.

Referencias: [instalar Python](https://docs.astral.sh/uv/guides/install-python/) y [sincronizar el entorno](https://docs.astral.sh/uv/concepts/projects/sync/).

## 4. Configurar el archivo .env

Si ya tienes un `.env`, conserva sus valores y revisa que esté en:

```text
src/password_manager/.env
```

Para una instalación nueva, crea ese archivo usando este esquema y reemplaza los valores de ejemplo:

```dotenv
ADMIN_NAME=tu_usuario
ADMIN_PASSWORD="REEMPLAZAR_POR_TU_CONTRASENA"
ADMIN_CODIGN="REEMPLAZAR_POR_UN_SECRETO_ALEATORIO"
FLASK_SECRET="REEMPLAZAR_POR_OTRO_SECRETO_ALEATORIO"
```

| Variable | Uso |
| --- | --- |
| `ADMIN_NAME` | Usuario para iniciar sesión |
| `ADMIN_PASSWORD` | Contraseña para iniciar sesión |
| `ADMIN_CODIGN` | Secreto del que se deriva la clave para cifrar los datos |
| `FLASK_SECRET` | Clave para firmar las cookies de sesión |
| `DATA_FILE` | Ruta opcional para guardar el JSON en otra ubicación |

El nombre `ADMIN_CODIGN` se conserva exactamente así por compatibilidad con tu código anterior.

Para generar un secreto, ejecuta:

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

En una instalación nueva, ejecútalo dos veces y usa un resultado distinto para `ADMIN_CODIGN` y `FLASK_SECRET`.

**Si ya guardaste contraseñas, conserva el valor anterior de `ADMIN_CODIGN`.** Cambiarlo no vuelve a cifrar los registros y hará que la aplicación no pueda descifrarlos. Cambiar `ADMIN_PASSWORD` modifica el acceso, pero no cambia la clave de cifrado.

Si omites `DATA_FILE`, se usa `src/password_manager/Data_P.json`. Para otra ubicación, es preferible una ruta absoluta. Una ruta relativa se interpreta desde el directorio donde inicias el proceso.

Las variables que ya estén definidas en el entorno tienen prioridad sobre el `.env`. Reinicia la aplicación después de cambiar la configuración.

## 5. Ejecutar la aplicación

Desde la raíz del proyecto:

```bash
uv run password-manager
```

También puedes iniciar el paquete con:

```bash
uv run python -m password_manager
```

Abre en el navegador:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

Inicia sesión con los valores de `ADMIN_NAME` y `ADMIN_PASSWORD`. Para detener el servidor, pulsa **Ctrl+C** en la terminal.

Para los siguientes arranques basta con `uv run password-manager`: uv comprueba el entorno antes de ejecutar el comando.

Referencia: [ejecutar comandos con uv](https://docs.astral.sh/uv/concepts/projects/run/).

## 6. Por qué se usan imports con punto

En este código:

```python
from . import create_app
```

El punto significa «desde el paquete actual». Importa `create_app` desde el `__init__.py` de `password_manager`.

Este otro ejemplo importa desde un módulo del mismo paquete:

```python
from .config import load_config
```

Ejecutar con `uv run python -m password_manager` permite que Python reconozca ese contexto de paquete. Ejecutar directamente el archivo interno con `python src/password_manager/password_manager.py` puede producir un error de importación relativa.

## 7. Uso del gestor

- **Agregar:** guarda nombre, enlace, correo y contraseña.
- **Buscar:** filtra por nombre, correo, enlace o contraseña.
- **Editar:** actualiza los campos y conserva hasta dos contraseñas anteriores cuando cambia la contraseña.
- **Generar:** crea una contraseña con las opciones elegidas.
- **Exportar CSV:** descarga las credenciales con las contraseñas en texto legible.
- **Importar CSV:** requiere columnas `name` y `password`; admite `link` y `email`. Las filas sin nombre o contraseña se omiten.
- **Exportar JSON:** descarga los registros con contraseñas e historial cifrados; nombre, correo y enlace siguen siendo legibles.

Para recuperar un respaldo JSON, detén la aplicación, conserva una copia del archivo actual y coloca el respaldo en la ruta de `DATA_FILE`. Debes usar el mismo `ADMIN_CODIGN` con el que se cifró el respaldo. La interfaz no incluye importación de JSON.

## 8. Problemas frecuentes

| Problema | Qué revisar |
| --- | --- |
| `uv` no se reconoce | Reabre la terminal y verifica que la instalación haya añadido uv al `PATH`. |
| No se encuentra `pyproject.toml` | Sitúate en la raíz del proyecto. |
| Python incompatible | Ejecuta `uv python install 3.14`, `uv python pin 3.14` y `uv sync`. |
| No se encuentra `password-manager` | Revisa `[project.scripts]` y ejecuta `uv sync`. |
| `attempted relative import with no known parent package` | Usa `uv run password-manager` o `uv run python -m password_manager`. |
| `TemplateNotFound` | Comprueba que `templates/` esté junto a `__init__.py` y contenga los HTML originales. |
| Credenciales incorrectas | Revisa el `.env` del paquete y posibles variables del entorno que lo sobrescriban. |
| No se pudo acceder a los datos | Comprueba el JSON, sus permisos y el valor original de `ADMIN_CODIGN`; conserva el archivo antes de modificarlo. |
| El puerto 5000 está ocupado | Detén la otra instancia o ejecuta `uv run flask --app password_manager:create_app run --port 5001` y abre el puerto 5001. |

## Alcance de esta versión

El comando principal inicia el servidor local de Flask en `127.0.0.1`, con depuración desactivada. El repositorio JSON coordina operaciones dentro de una instancia; para varios procesos necesita otro mecanismo de persistencia.

En la preparación del código se verificaron la sintaxis y las operaciones de almacenamiento. No se ejecutó la aplicación completa en el entorno de entrega porque sus dependencias no estaban disponibles. Después de instalar con uv, comprueba el inicio de sesión y las operaciones con una entrada de prueba antes de usar datos reales.
