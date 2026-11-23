# Backend de AlimentoSolidario Huancayo

API de AlimentoSolidario Huancayo con FastAPI, SQL Server y `pyodbc`.

## Objetivo
- Exponer APIs REST para usuarios, donaciones, solicitudes y entregas.
- Guardar usuarios, donaciones, solicitudes y entregas en SQL Server.
- Crear la base de datos, el esquema y los datos de demostración al iniciar.

## Estructura

- `app/apis`: routers y endpoints REST.
- `app/schemas`: validaciones con Pydantic.
- `app/services`: lógica de negocio.
- `app/repositories`: consultas y operaciones SQL.
- `app/data`: carga inicial de los datos de demostración.
- `app/core`: configuración, conexión a SQL Server y JWT.
- `sql/create_schema.sql`: esquema relacional idempotente.

## Requisitos
- Python 3.14+
- `uv`
- SQL Server instalado y en ejecución.
- En Windows, ODBC Driver 18 for SQL Server y acceso autorizado a la instancia.

## Instalación

```bash
cd backend
uv sync
```

La configuración local está documentada en `backend/.env.example`. Se usa
autenticación integrada de Windows (`DB_TRUSTED_CONNECTION=true`); la cuenta
de Windows debe tener permiso para crear bases de datos. Para autenticación
de SQL Server, define `DB_TRUSTED_CONNECTION=false`, `DB_USER` y `DB_PASSWORD`
en `backend/.env`. No guardes contraseñas en el repositorio.

Al iniciar, el backend crea la base configurada en `DB_NAME` (por defecto
`alimento_solidario`), crea las tablas y sus claves foráneas, y carga los
usuarios demo únicamente cuando la tabla de usuarios está vacía. Reiniciar
el servidor no borra los datos. El usuario SQL necesita permiso para crear
la base y modificar su esquema.

La instancia local puede usar Shared Memory sin activar TCP/IP. Si SQL Server
está detenido, abre PowerShell como administrador y ejecuta una vez:

```powershell
Start-Service MSSQLSERVER
```

ODBC Driver 18 cifra la conexión. La configuración de desarrollo confía en el
certificado local; en producción, instala un certificado confiable y configura
`DB_TRUST_SERVER_CERTIFICATE=false`.

Si `API_HOST` no es loopback, el arranque exige una `SECRET_KEY` aleatoria de
al menos 32 bytes y `DB_TRUST_SERVER_CERTIFICATE=false`. Genera la clave con
`python -c "import secrets; print(secrets.token_urlsafe(48))"` y guárdala solo
en `backend/.env`; nunca publiques ese valor.

## Ejecutar servidor

```bash
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

o

```bash
uv run python main.py
```

> En Windows con la ruta del proyecto dentro de OneDrive, el ejecutable
> `uv run uvicorn` puede fallar con `uv trampoline failed to canonicalize
> script path`. La forma estable es invocar el módulo con `python -m uvicorn`.

## Configuración

El backend carga `backend/.env` al iniciar. Toma como referencia
`backend/.env.example`.

| Variable | Uso | Valor por defecto |
|---|---|---|
| `APP_NAME`, `APP_DESCRIPTION`, `APP_VERSION` | Metadatos de FastAPI | Ver `.env.example` |
| `API_HOST`, `API_PORT` | Host y puerto usados por `main.py` | `127.0.0.1`, `8000` |
| `CORS_ORIGINS` | Orígenes permitidos, separados por comas | `http://localhost:4200,http://127.0.0.1:4200` |
| `SECRET_KEY` | Firma de los JWT | Demo solo para loopback; obligatoria y segura para host público |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Vigencia del token | `1440` |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_DRIVER` | Dirección, puerto, base de datos y controlador SQL Server | `(local)`, `1433`, `alimento_solidario`, ODBC 18 |
| `DB_TRUSTED_CONNECTION` | Usa la cuenta de Windows (`false` usa `DB_USER` y `DB_PASSWORD`) | `true` |
| `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE` | Cifrado TLS y certificado del servidor | `true`, `true` |
| `DB_CONNECTION_TIMEOUT` | Tiempo máximo para establecer la conexión en segundos | `5` |

Para habilitar otro origen de Angular basta con agregarlo a `CORS_ORIGINS` y
reiniciar el servidor (por ejemplo `http://localhost:4300`).

La instancia local `(local)` no requiere que TCP/IP esté activado; para un
servidor remoto, habilita TCP/IP y establece su dirección en `DB_HOST`.

## Documentación Swagger

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## Comprobar la conexión y persistencia

Desde `backend`, ejecuta:

```bash
uv run python -m scripts.database_smoke_test
```

Comprueba SQL Server, crea un usuario temporal, lo lee desde una conexión
nueva y lo elimina. La API ofrece `GET http://127.0.0.1:8000/api/health/database`
para confirmar la conexión activa. Con el backend en ejecución,
`uv run python -m scripts.smoke_test` valida los endpoints y la conexión a la
base de datos utilizados por Angular.

## CRUD y pruebas

- Donaciones, solicitudes y usuarios admiten consulta, creación, actualización y baja lógica.
- `DELETE` cancela donaciones y solicitudes; solo permite transiciones desde estados activos.
- El registro público solo acepta los roles `negocio`, `comedor` y `voluntario`; `rol=admin` se rechaza con HTTP 422.
- Solo un administrador puede listar, editar, cambiar rol/estado o desactivar usuarios. La cuenta admin inicial proviene del seed; otros admins se asignan por un administrador autenticado.
- `GET /api/usuarios?rol=voluntario` filtra por rol mediante un parámetro SQL.
- Las pruebas unitarias se ejecutan con `uv run pytest` y exigen al menos
  30 % de cobertura del paquete `app`.
- Con el backend y SQL Server activos, `uv run python -m scripts.smoke_test`
  valida flujos de API y roles.

## Flujo operativo de 7 pasos

1. El negocio publica una donación y queda disponible.
2. El comedor solicita la donación y elige `recoger`, `trasladar` o `ambos`.
3. El negocio aprueba o rechaza; al aprobar ajusta el apoyo y se crea una entrega abierta.
4. Un voluntario disponible acepta o pasa una misión abierta.
5. La aceptación pasa la misión a `aceptada` y genera avisos al comedor y, si corresponde, al negocio.
6. El voluntario marca `recogida`; el comedor confirma y la entrega pasa a `entregada`.
7. El admin consulta la cadena completa y puede intervenir ante problemas.

El teléfono solo se devuelve después de aprobar y únicamente a participantes
relacionados y al administrador.

## Endpoints principales

- `GET /api/dashboard/resumen`: contadores filtrados por el usuario y su rol.
- `GET /api/entregas/abiertas`: misiones abiertas excluyendo las descartadas por el voluntario.
- `GET /api/avisos/`: avisos propios del usuario autenticado.
- `PATCH /api/avisos/{id}/leer`: marca un aviso propio como leído.
- `PATCH /api/usuarios/me/disponible`: cambia la disponibilidad del voluntario autenticado.
- `POST /api/solicitudes/{id}/aprobar`: aprobación exclusiva del negocio propietario.
- `POST /api/solicitudes/{id}/rechazar`: rechazo exclusivo del negocio propietario.
- `POST /api/voluntarios/entregas/{id}/aceptar`: aceptación por voluntario disponible.
- `POST /api/voluntarios/entregas/{id}/recogido`: transición de aceptada a recogida.
- `POST /api/voluntarios/entregas/{id}/confirmar`: recepción confirmada por el comedor.

## Nota importante

Las cuentas demo y sus contraseñas están documentadas en
`Frontend/README.md`. Cámbialas antes de exponer la aplicación fuera del
entorno local.

## Auditoría técnica — 23 noviembre de 2026

Estado verificable del sistema en el entorno local:

- Backend: 68 pruebas aprobadas, 59.49 % de cobertura del paquete `app`.
- Frontend: 11 archivos de prueba y 29 pruebas aprobadas.
- Compilación Angular: exitosa.
- SQL Server: esquema actualizado sin eliminar filas; los conteos de las seis
  tablas se mantuvieron en 7 usuarios, 5 donaciones, 9 solicitudes, 3 entregas,
  0 rechazos y 8 avisos.
- Prueba HTTP en una base temporal recién creada: 22 de 22 comprobaciones
  aprobadas, incluidos registro/login, donación, solicitud, aprobación, misión, avisos,
  confirmación, dashboard y permisos por rol.
- Salud operativa de la base temporal: `GET /api/health/database` respondió `ok`.

La prueba HTTP se ejecuta en una base temporal descartable, no sobre la base
configurada del proyecto. El script restaura disponibilidad y misiones demo, y
limpia las filas propias aun cuando falle una etapa.
