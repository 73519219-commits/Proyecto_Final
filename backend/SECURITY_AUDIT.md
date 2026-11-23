# Auditoría de seguridad

Actualización: 23 noviembre de 2026.

Alcance: consultas de `app/repositories`, hashing de contraseñas, dependencias
de rol de los endpoints, aislamiento de datos por usuario y usos de
`bypassSecurityTrust*` en Angular. El reporte no modifica el contrato HTTP.

## Verificación ejecutada

- Backend: 68 pruebas aprobadas; cobertura total 59.49 %.
- Frontend: 11 archivos de prueba y 29 pruebas aprobadas.
- Prueba HTTP completa en base temporal: 22/22 comprobaciones aprobadas.
- Esquema actualizado en la base configurada sin modificar el número de filas;
  integración HTTP ejecutada en una base SQL temporal aislada.
- No se encontraron llamadas a `bypassSecurityTrust*` en `Frontend/src`.

## SQL en repositorios

No se encontró SQL que interpole valores externos sin parametrizarlos. Los
valores dinámicos se envían con `?`; los `UPDATE` dinámicos construyen nombres
de columna desde listas permitidas y mantienen los valores como parámetros:

- [donacion_repository.py:57](./app/repositories/donacion_repository.py#L57)
- [solicitud_repository.py:45](./app/repositories/solicitud_repository.py#L45)
- [usuario_repository.py:69](./app/repositories/usuario_repository.py#L69)
- [entrega_repository.py:52](./app/repositories/entrega_repository.py#L52)
- Filtro de rol parametrizado: [usuario_repository.py:17](./app/repositories/usuario_repository.py#L17)

Las consultas sin `?` no reciben valores del usuario; son listados o usan
predicados constantes: [donacion_repository.py:11](./app/repositories/donacion_repository.py#L11),
[donacion_repository.py:94](./app/repositories/donacion_repository.py#L94),
[solicitud_repository.py:11](./app/repositories/solicitud_repository.py#L11),
[usuario_repository.py:19](./app/repositories/usuario_repository.py#L19),
[entrega_repository.py:19](./app/repositories/entrega_repository.py#L19) y
[entrega_repository.py:84](./app/repositories/entrega_repository.py#L84).

**Fix mínimo:** no se requiere para prevenir inyección en estas consultas.
Conservar las listas de columnas permitidas y los placeholders al añadir
filtros nuevos; los estados literales actuales son constantes.

## Contraseñas

- Librería: `bcrypt==4.1.2`.
- Hash y verificación: [seguridad.py:21](./app/core/seguridad.py#L21) y
  [seguridad.py:26](./app/core/seguridad.py#L26).
- Alta y cambio de contraseña: [usuario_service.py:26](./app/services/usuario_service.py#L26),
  [usuario_service.py:63](./app/services/usuario_service.py#L63); el login
  verifica el hash en [usuario_service.py:89](./app/services/usuario_service.py#L89).
- Seed demo: cada contraseña se transforma con `hash_password` antes del
  `executemany` en [demo_data.py:35](./app/data/demo_data.py#L35).

## Roles por endpoint

Los endpoints con `get_current_user` requieren autenticación y usuario activo.

| Endpoint | Acceso |
|---|---|
| `POST /api/auth/registro` | Público; solo acepta `negocio`, `comedor` o `voluntario` ([usuarios.py:19](./app/apis/usuarios.py#L19), [usuario.py:24](./app/schemas/usuario.py#L24)). |
| `POST /api/auth/login` | Público ([usuarios.py:24](./app/apis/usuarios.py#L24)). |
| `GET /api/usuarios` | Solo `admin` ([usuarios.py:37](./app/apis/usuarios.py#L37)). |
| `GET /api/usuarios/me` | Cualquier usuario autenticado ([usuarios.py:45](./app/apis/usuarios.py#L45)). |
| `PUT/PATCH/DELETE /api/usuarios/{id}` | Solo `admin` ([usuarios.py:50](./app/apis/usuarios.py#L50), [usuarios.py:60](./app/apis/usuarios.py#L60)). |
| `GET /api/donaciones/` | Autenticado: `admin` ve todas; `negocio` las propias; `comedor` y `voluntario` las disponibles; otros reciben 403 ([donaciones.py:12](./app/apis/donaciones.py#L12)). |
| `GET /api/donaciones/disponibles` | `admin`, `comedor` o `voluntario` ([donaciones.py:23](./app/apis/donaciones.py#L23)). |
| `POST /api/donaciones/` | `admin` o `negocio`; el negocio solo puede usar su propio ID ([donaciones.py:30](./app/apis/donaciones.py#L30)). |
| `PUT/DELETE /api/donaciones/{id}` | `admin` o negocio propietario ([donaciones.py:40](./app/apis/donaciones.py#L40), [donaciones.py:52](./app/apis/donaciones.py#L52)). |
| `GET /api/solicitudes/` | Autenticado: `admin` ve todas, `comedor` solo las propias; otros reciben 403 ([solicitudes.py:12](./app/apis/solicitudes.py#L12)). |
| `POST /api/solicitudes/` | `admin` o `comedor`; el comedor solo puede crear para sí mismo ([solicitudes.py:21](./app/apis/solicitudes.py#L21)). |
| `PUT/DELETE /api/solicitudes/{id}` | `admin` o comedor propietario ([solicitudes.py:28](./app/apis/solicitudes.py#L28), [solicitudes.py:47](./app/apis/solicitudes.py#L47)). |
| `PATCH /api/solicitudes/{id}/estado` | Solo `admin` ([solicitudes.py:36](./app/apis/solicitudes.py#L36)). |
| `POST /api/solicitudes/{id}/aprobar` | Solo el negocio propietario de la donación; puede ajustar `tipo_apoyo` ([solicitudes.py](./app/apis/solicitudes.py)). |
| `POST /api/solicitudes/{id}/rechazar` | Solo el negocio propietario de la donación ([solicitudes.py](./app/apis/solicitudes.py)). |
| `GET /api/voluntarios/entregas` | `admin` ve todas; `voluntario` solo las asignadas a sí mismo ([voluntarios.py:13](./app/apis/voluntarios.py#L13)). |
| `GET /api/voluntarios/entregas/abiertas` | Solo voluntarios activos; excluye misiones que ese voluntario indicó pasar ([voluntarios.py](./app/apis/voluntarios.py)). |
| `POST /api/voluntarios/entregas/{id}/aceptar` | `admin` o `voluntario`; el voluntario no puede tomar una entrega asignada a otra persona ([voluntarios.py:22](./app/apis/voluntarios.py#L22)). |
| `POST /api/voluntarios/entregas/{id}/pasar` | Solo el voluntario autenticado; registra un pase sin asignar la misión ([voluntarios.py](./app/apis/voluntarios.py)). |
| `POST /api/voluntarios/entregas/{id}/recogido` | Solo el voluntario asignado ([voluntarios.py](./app/apis/voluntarios.py)). |
| `POST /api/voluntarios/entregas/{id}/entregado` | Solo el comedor receptor, que confirma la entrega ([voluntarios.py](./app/apis/voluntarios.py)). |
| `POST /api/voluntarios/entregas/{id}/confirmar` | Solo el comedor propietario de la solicitud ([voluntarios.py](./app/apis/voluntarios.py)). |
| `PATCH /api/voluntarios/entregas/{id}/estado` | `admin` o `voluntario`; este último solo sus entregas ([voluntarios.py:35](./app/apis/voluntarios.py#L35)). |
| `GET /api/health/database` | Público, sin dependencia de autenticación ([health.py:11](./app/apis/health.py#L11)). |
| `GET /api/dashboard/resumen` | Autenticado; devuelve contadores filtrados por rol y usuario. Los no-admin no reciben totales globales ([dashboard.py](./app/apis/dashboard.py)). |
| `GET /api/entregas/abiertas` | `voluntario`, `comedor`, `negocio` o `admin`; el voluntario debe estar disponible y no puede ver misiones que descartó ([entregas.py](./app/apis/entregas.py)). |
| `GET /api/avisos/` | Cualquier usuario autenticado recibe únicamente avisos cuyo `usuario_destino` coincide con su ID ([avisos.py](./app/apis/avisos.py)). |
| `PATCH /api/avisos/{id}/leer` | Cualquier usuario autenticado puede marcar leído solo un aviso propio; otro ID devuelve 404 ([avisos.py](./app/apis/avisos.py), [aviso_repository.py](./app/repositories/aviso_repository.py)). |
| `PATCH /api/usuarios/me/disponible` | Solo `voluntario`; actualiza únicamente la disponibilidad del usuario autenticado ([usuarios.py](./app/apis/usuarios.py)). |
| `POST /api/voluntarios/entregas/{id}/aceptar` | Solo voluntario disponible; el service rechaza si ya tiene una misión activa ([voluntarios.py](./app/apis/voluntarios.py), [voluntario_service.py](./app/services/voluntario_service.py)). |
| `GET /api/voluntarios/entregas/abiertas` | Solo voluntario disponible; las misiones descartadas quedan excluidas por filtro SQL parametrizado ([voluntarios.py](./app/apis/voluntarios.py), [entrega_repository.py](./app/repositories/entrega_repository.py)). |

### Hallazgo prioritario — RESUELTO

`UsuarioCreate` restringe el campo `rol` a `negocio`, `comedor` y `voluntario`
([usuario.py:24](./app/schemas/usuario.py#L24)); un registro con `rol="admin"`
se rechaza con HTTP 422 antes de llegar al servicio. La prueba verifica tanto
el rechazo como el enum publicado en OpenAPI
([test_api.py](./tests/test_api.py)). El rol administrador puede asignarse a
una cuenta existente mediante PUT/PATCH, endpoints que exigen `admin`
([usuarios.py:50](./app/apis/usuarios.py#L50)); la baja y edición de usuarios
también son exclusivas de ese rol.

**Fix aplicado:** validación en el schema de registro, sin cambiar el formato
del cuerpo HTTP. Las pruebas también confirman que un usuario no administrador
no puede modificar rol ni estado, propios o ajenos.

## Frontend

No se encontraron llamadas a `bypassSecurityTrust*` bajo `Frontend/src`.

## Migración del flujo nuevo

- `dbo.usuarios.disponible` es exclusivo del estado operativo de voluntarios y se
  administra mediante el contrato de usuario existente.
- `dbo.solicitudes.necesita_apoyo` y `dbo.entregas.tipo` están restringidos a
  `recoger`, `trasladar` o `ambos`.
- Los estados de entrega admitidos son `abierta`, `aceptada`, `recogida`,
  `entregada` y `cancelada`. El service rechaza cualquier transición fuera de
  `abierta -> aceptada -> recogida -> entregada`.
- Las migraciones usan `COL_LENGTH`, `IF OBJECT_ID` y cambios de restricción
  idempotentes; no eliminan datos existentes ni vuelven a ejecutar el seed demo
  cuando ya existen usuarios.
