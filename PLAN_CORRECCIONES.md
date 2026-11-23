# Auditoría técnica y plan de correcciones — AlimentoSolidario

**Actualizado:** 23 de noviembre de 2026
**Alcance:** auditoría estática inicial y correcciones posteriores del backend FastAPI, Angular, SQL Server, configuración y pruebas. Se protegieron los datos existentes; los flujos HTTP se ejecutaron solo en una base SQL temporal.

## Resumen ejecutivo

Se corrigieron los defectos de consistencia detectados en el primer informe,
además de un fallo de DDL descubierto al ejecutar una integración real: SQL
Server rechazaba un índice filtrado sobre una columna calculada y la
inicialización no consumía los resultados posteriores del lote. El esquema
ahora crea las seis tablas requeridas, falla explícitamente ante anomalías y
aplica un índice filtrado sobre columnas físicas.

Verificación final: backend **68 pruebas aprobadas** (59.49 % de cobertura);
frontend **29 pruebas aprobadas**; build de producción Angular exitoso; flujo
HTTP completo en base temporal **22/22**. El esquema actualizado se aplicó a
`alimento_solidario`; los conteos de usuarios, donaciones, solicitudes,
entregas, rechazos y avisos permanecieron en **7, 5, 9, 3, 0 y 8**. No se
eliminó ningún registro de esa base. La clave JWT local de demostración se
rotó por una aleatoria, lo que requiere iniciar sesión de nuevo.

**Estado global:** hallazgos corregidos y verificados en los ámbitos indicados
abajo; se identifican expresamente las verificaciones pendientes de
concurrencia real, navegador autenticado y despliegue productivo.

## Hallazgos

### A-01 — Clave JWT de demostración usada como valor por defecto

- **Prioridad:** Crítico
- **Estado:** Corregido. `.env.example` ya no publica la clave demo; se rotó la clave local. La API rechaza una clave demo/corta o TLS de SQL no validado al exponerse en una interfaz no-loopback. La validación se probó; un despliegue público no se realizó.
- **Ubicación:** [`backend/app/core/config.py:85`](./backend/app/core/config.py#L85), [`backend/app/main.py:21`](./backend/app/main.py#L21), [`backend/.env.example:13`](./backend/.env.example#L13).
- **Problema:** si no se define `SECRET_KEY`, el backend firma JWT con un valor conocido y publicado en el ejemplo de configuración.
- **Consecuencia:** si la API se expone con esa configuración, un tercero que conozca la clave puede falsificar tokens, incluidos tokens con rol administrador.
- **Recomendación:** fallar al iniciar en entornos no locales cuando la clave no esté definida o sea la de demostración; generar una clave aleatoria de alta entropía y rotarla en producción. No reutilizar el valor del ejemplo.

### A-02 — La inicialización de la aplicación puede borrar entregas existentes

- **Prioridad:** Alto
- **Estado:** Corregido y aplicado. Se retiró la eliminación automática. El esquema informa de duplicados/anomalías sin borrarlos; la migración se ejecutó primero en una base temporal y después en la base configurada, con preflight y conteos idénticos antes/después.
- **Ubicación:** [`backend/app/core/database.py:96`](./backend/app/core/database.py#L96), [`backend/sql/create_schema.sql:119`](./backend/sql/create_schema.sql#L119), [`backend/sql/create_schema.sql:134`](./backend/sql/create_schema.sql#L134).
- **Problema:** el lifespan de FastAPI llama `initialize_database()` en cada inicio. El script de esquema elimina filas de `dbo.entregas` duplicadas por `solicitud_id` y también elimina sus filas asociadas de `rechazos_mision`.
- **Consecuencia:** iniciar o reiniciar el backend puede borrar historial operativo sin confirmación, respaldo ni reporte de qué registros fueron descartados.
- **Recomendación:** sacar la depuración destructiva del arranque automático. Preparar una migración explícita, con respaldo, revisión previa del conjunto afectado y ejecución aprobada por el operador. La inicialización normal debe preservar los datos.

### A-03 — Cancelar solicitudes por PUT/PATCH evita la transacción de cancelación

- **Prioridad:** Alto
- **Estado:** Corregido en servicio y repositorio: la cancelación pasa por una transacción que sincroniza solicitud, entrega y donación. Pruebas unitarias pasadas; no se ejecutó el caso de cancelación HTTP en la base temporal.
- **Ubicación:** [`backend/app/apis/solicitudes.py:40`](./backend/app/apis/solicitudes.py#L40), [`backend/app/services/solicitud_service.py:128`](./backend/app/services/solicitud_service.py#L128), [`backend/app/services/solicitud_service.py:146`](./backend/app/services/solicitud_service.py#L146), [`backend/app/repositories/solicitud_repository.py:237`](./backend/app/repositories/solicitud_repository.py#L237).
- **Problema:** `PUT /api/solicitudes/{id}` permite establecer `estado="cancelada"` y el PATCH administrativo también cambia estados mediante una actualización simple. Ambos caminos evitan `cancelar_atomica()`, que es el método que sincroniza la entrega relacionada y el estado de la donación.
- **Consecuencia:** una solicitud puede quedar cancelada mientras su misión siga abierta/activa y la donación siga reservada.
- **Recomendación:** hacer que todo cambio a cancelada pase por la operación transaccional; restringir estados modificables por PUT/PATCH y aplicar las mismas reglas a todos los caminos de escritura.

### A-04 — Solicitudes aprobadas pueden editarse sin conservar las invariantes

- **Prioridad:** Alto
- **Estado:** Corregido: solo se editan solicitudes pendientes, no se permiten cambios de estado o relaciones por PUT, y Angular ya no ofrece editar solicitudes aprobadas. Pruebas backend y build frontend pasaron.
- **Ubicación:** [`backend/app/services/solicitud_service.py:98`](./backend/app/services/solicitud_service.py#L98), [`backend/app/apis/solicitudes.py:40`](./backend/app/apis/solicitudes.py#L40), [`Frontend/src/app/pages/solicitudes/solicitudes.html:84`](./Frontend/src/app/pages/solicitudes/solicitudes.html#L84).
- **Problema:** el PUT acepta `donacion_id`, `comedor_id` y `cantidad_solicitada` sin limitar la edición al estado pendiente. El repositorio persiste esos campos directamente. No vuelve a comprobar la suma aprobada por donación ni sincroniza la entrega existente.
- **Consecuencia:** se puede cambiar el comedor o donación de una solicitud ya aprobada, o elevar su cantidad y superar lo donado; la entrega asociada puede quedar vinculada a información distinta de la que se aprobó.
- **Recomendación:** bloquear cambios de relación y cantidad después de la aprobación (salvo flujo explícito y transaccional); validar roles, existencia y cantidad disponible dentro de la misma transacción de escritura.

### A-05 — Aceptación y cambios de misión no son atómicos frente a concurrencia

- **Prioridad:** Alto
- **Estado:** Corregido en transacciones e índice único SQL; aceptación y estados críticos se comprobaron en SQL Server temporal. No se ejecutó una prueba de estrés concurrente de dos conexiones.
- **Ubicación:** [`backend/app/services/voluntario_service.py:72`](./backend/app/services/voluntario_service.py#L72), [`backend/app/repositories/entrega_repository.py:19`](./backend/app/repositories/entrega_repository.py#L19), [`backend/app/repositories/entrega_repository.py:80`](./backend/app/repositories/entrega_repository.py#L80), [`backend/sql/create_schema.sql:199`](./backend/sql/create_schema.sql#L199).
- **Problema:** aceptar una misión lee la entrega, cuenta misiones activas y luego actualiza mediante operaciones SQL separadas. La actualización no incluye una condición `estado='abierta'`; tampoco hay una restricción que impida que un voluntario termine con más de una misión activa.
- **Consecuencia:** dos voluntarios pueden recibir respuestas de aceptación para la misma misión y uno sobrescribir al otro; solicitudes simultáneas del mismo voluntario pueden asignarle varias misiones activas. La transición de estado controlada también lee y actualiza en pasos separados.
- **Recomendación:** trasladar comprobaciones y asignación a una transacción con bloqueo/actualización condicional; añadir restricciones SQL que expresen las invariantes activas que el modelo permita y probar carreras con dos conexiones.

### A-06 — Rechazar una solicitud puede competir con su aprobación

- **Prioridad:** Alto
- **Estado:** Corregido: rechazo serializable con bloqueo y condición de pendiente, alineado con aprobación. Pruebas unitarias pasaron; no se simuló la carrera simultánea ni se implementó outbox para avisos.
- **Ubicación:** [`backend/app/services/solicitud_service.py:205`](./backend/app/services/solicitud_service.py#L205), [`backend/app/repositories/solicitud_repository.py:93`](./backend/app/repositories/solicitud_repository.py#L93).
- **Problema:** la aprobación usa una transacción serializable, pero el rechazo hace una lectura de estado y una actualización posterior que no condiciona el `UPDATE` a `estado='pendiente'`.
- **Consecuencia:** un rechazo iniciado mientras otra petición aprueba puede cambiar a rechazada una solicitud que ya creó una entrega y reservó la donación; también puede devolver respuestas incoherentes a ambas operaciones.
- **Recomendación:** serializar rechazo y aprobación con el mismo mecanismo de bloqueo/condición de estado y registrar el aviso dentro de una estrategia transaccional o de outbox.

### A-07 — El administrador puede dejar una entrega aceptada sin voluntario asignado

- **Prioridad:** Medio
- **Estado:** Corregido: la aceptación genérica está bloqueada y la asignación solo se realiza por la operación atómica del voluntario. Suite backend e integración HTTP pasaron.
- **Ubicación:** [`backend/app/apis/voluntarios.py:105`](./backend/app/apis/voluntarios.py#L105), [`backend/app/services/voluntario_service.py:112`](./backend/app/services/voluntario_service.py#L112), [`backend/app/repositories/entrega_repository.py:19`](./backend/app/repositories/entrega_repository.py#L19).
- **Problema:** el PATCH de estado permite a un administrador cambiar una entrega abierta a `aceptada`; el servicio solo cambia `estado` y no exige ni asigna `voluntario_id`.
- **Consecuencia:** la misión deja de aparecer como abierta, pero no queda asociada a un voluntario que pueda recogerla o completarla.
- **Recomendación:** hacer que “aceptar” sea la única operación que combine asignación y cambio a aceptada; impedir estados que requieren actor/asignación desde el PATCH genérico.

### A-08 — La ruta de avisos de voluntarios usa columnas que no existen en el esquema vigente

- **Prioridad:** Medio
- **Estado:** Corregido y probado: el endpoint legacy ahora consulta el repositorio de avisos vigente; la ruta respondió 200 en la integración temporal.
- **Ubicación:** [`backend/app/apis/voluntarios.py:40`](./backend/app/apis/voluntarios.py#L40), [`backend/app/services/voluntario_service.py:66`](./backend/app/services/voluntario_service.py#L66), [`backend/app/repositories/aviso_repository.py:32`](./backend/app/repositories/aviso_repository.py#L32).
- **Problema:** `GET /api/voluntarios/avisos` consulta `usuario_id`, `entrega_id` y `creado_en`. La tabla actual `dbo.avisos` define `usuario_destino`, `tipo`, `referencia_id` y `created_at`.
- **Consecuencia:** la ruta falla con error SQL en una base creada con el esquema actual. Angular usa `/api/avisos/`, por lo que este endpoint no se ejercitó en la interfaz revisada.
- **Recomendación:** eliminar la implementación obsoleta si no forma parte del contrato o hacer que use `AvisoRepository` y el esquema actual; añadir una prueba de integración para cada ruta de avisos.

### A-09 — El seed crea una solicitud pendiente con una entrega ya aceptada

- **Prioridad:** Medio
- **Estado:** Corregido y probado: el seed crea solicitud aprobada, donación reservada y misión aceptada sin fecha de entrega. La inicialización desde una base temporal vacía creó tablas y datos coherentes.
- **Ubicación:** [`backend/app/data/demo_data.py:19`](./backend/app/data/demo_data.py#L19), [`backend/app/data/demo_data.py:58`](./backend/app/data/demo_data.py#L58), [`backend/app/data/demo_data.py:66`](./backend/app/data/demo_data.py#L66).
- **Problema:** el seed crea la solicitud con estado `pendiente` y a continuación crea para ella una entrega con estado `aceptada` y voluntario asignado.
- **Consecuencia:** la cadena de demostración no respeta la regla de que la aprobación crea la misión; dashboard y pantallas pueden presentar estados contradictorios.
- **Recomendación:** construir datos demo que representen una transición válida completa, o dejar la solicitud pendiente sin entrega y documentar el estado inicial esperado.

### A-10 — Errores HTTP del dashboard se silencian y sus contadores quedan obsoletos

- **Prioridad:** Medio
- **Estado:** Corregido en Angular: se muestran errores de resumen/listas/avisos y se recargan contadores tras operaciones. Pruebas y build pasaron; no se hizo recorrido visual autenticado en navegador.
- **Ubicación:** [`Frontend/src/app/pages/dashboard/dashboard.ts:242`](./Frontend/src/app/pages/dashboard/dashboard.ts#L242), [`Frontend/src/app/pages/dashboard/dashboard.ts:255`](./Frontend/src/app/pages/dashboard/dashboard.ts#L255), [`Frontend/src/app/components/navbar/navbar.ts:47`](./Frontend/src/app/components/navbar/navbar.ts#L47).
- **Problema:** varias cargas y acciones usan `error: () => undefined`; el resumen sustituye el error por un objeto vacío. Tras aprobar/rechazar, confirmar o cambiar una misión no se vuelve a solicitar el resumen.
- **Consecuencia:** errores de red/permisos se muestran como listas vacías o contadores cero; las tarjetas y el “siguiente paso” pueden quedar desactualizados hasta recargar la página.
- **Recomendación:** exponer estados de carga/error con `mensajeError`, y refrescar los datos dependientes después de cada operación exitosa.

### A-11 — La configuración de producción apunta a loopback

- **Prioridad:** Medio
- **Estado:** Corregido en configuración: producción usa `/api` y requiere proxy same-origin. El build no contiene URLs loopback; el proxy de despliegue no se verificó.
- **Ubicación:** [`Frontend/src/environments/environment.ts:7`](./Frontend/src/environments/environment.ts#L7).
- **Problema:** el build de producción usa `http://127.0.0.1:8000/api`.
- **Consecuencia:** en un navegador de producción, `127.0.0.1` apunta al equipo del usuario, no al servidor desplegado; las llamadas API fallan salvo que la URL se reemplace durante el proceso de despliegue.
- **Recomendación:** inyectar la URL por configuración de entorno de despliegue y verificar que el artefacto publicado no contenga el loopback.

### A-12 — Registro duplicado concurrente puede terminar en error 500

- **Prioridad:** Medio
- **Estado:** Corregido: las violaciones de correo único se traducen a HTTP 409; una prueba simula la colisión ocurrida entre consulta e inserción. No se ejecutó carga concurrente contra SQL Server.
- **Ubicación:** [`backend/app/services/usuario_service.py:17`](./backend/app/services/usuario_service.py#L17), [`backend/app/repositories/usuario_repository.py:50`](./backend/app/repositories/usuario_repository.py#L50), [`backend/app/repositories/usuario_repository.py:74`](./backend/app/repositories/usuario_repository.py#L74), [`backend/sql/create_schema.sql:15`](./backend/sql/create_schema.sql#L15).
- **Problema:** el servicio comprueba primero si existe el correo y después inserta. El índice único evita duplicados, pero no se traduce la violación de unicidad que ocurre si dos registros compiten.
- **Consecuencia:** el segundo registro obtiene una excepción SQL no controlada en vez de una respuesta HTTP de conflicto legible.
- **Recomendación:** conservar la restricción única y mapear específicamente su violación a HTTP 409/400; probar dos altas simultáneas.

### A-13 — Las relaciones SQL validan existencia, pero no el rol del participante

- **Prioridad:** Medio
- **Estado:** Corregido en los servicios para altas y relaciones nuevas: se comprueban rol y estado de negocio/comedor. SQL sigue sin poder impedir una escritura manual directa con roles incompatibles.
- **Ubicación:** [`backend/app/services/donacion_service.py:18`](./backend/app/services/donacion_service.py#L18), [`backend/app/services/solicitud_service.py:50`](./backend/app/services/solicitud_service.py#L50), [`backend/sql/create_schema.sql:40`](./backend/sql/create_schema.sql#L40), [`backend/sql/create_schema.sql:61`](./backend/sql/create_schema.sql#L61).
- **Problema:** las claves foráneas comprueban que exista el usuario, pero no que `usuario_negocio_id` sea negocio o que `comedor_id` sea comedor. Un administrador puede enviar esos IDs en creación; el esquema no impide asociaciones entre roles incorrectos.
- **Consecuencia:** donaciones/solicitudes pueden quedar asociadas a cuentas que no pueden operar el flujo y desaparecer de los listados filtrados por rol.
- **Recomendación:** validar el rol y el estado del usuario relacionado en el servicio de escritura; añadir pruebas para IDs existentes con rol incorrecto.

### A-14 — La edición de donación permite reasignar propietario y estado sin reglas de transición

- **Prioridad:** Medio
- **Estado:** Corregido en servicio/API/UI: la creación empieza disponible; estados se cambian solo por operaciones válidas; negocios no transfieren propietario; cantidades no pueden quedar por debajo de lo aprobado. La integración principal pasó.
- **Ubicación:** [`backend/app/apis/donaciones.py:41`](./backend/app/apis/donaciones.py#L41), [`backend/app/schemas/donacion.py:25`](./backend/app/schemas/donacion.py#L25), [`backend/app/services/donacion_service.py:18`](./backend/app/services/donacion_service.py#L18), [`backend/app/services/donacion_service.py:49`](./backend/app/services/donacion_service.py#L49).
- **Problema:** el control de propietario se hace sobre la donación antes de la actualización, pero `DonacionUpdate` permite cambiar `usuario_negocio_id`, `estado` y cantidad. El servicio no valida la transición de estado ni el efecto de editar una donación que ya tiene solicitudes/entregas.
- **Consecuencia:** un negocio puede transferir la donación a otro ID o cambiar su estado/cantidad de forma que contradiga solicitudes aprobadas.
- **Recomendación:** no aceptar cambios de propietario desde cuentas de negocio; permitir estados solo por transiciones explícitas; validar en transacción las solicitudes y entregas relacionadas.

### A-15 — Las cifras de pruebas documentadas no coinciden con la ejecución actual

- **Prioridad:** Bajo
- **Estado:** Corregido: README backend/frontend y auditoría de seguridad actualizados con los resultados de esta ejecución y el aislamiento de las pruebas HTTP.
- **Ubicación:** [`backend/README.md:163`](./backend/README.md#L163), [`backend/SECURITY_AUDIT.md:11`](./backend/SECURITY_AUDIT.md#L11), [`Frontend/README.md:68`](./Frontend/README.md#L68).
- **Problema:** los documentos conservaban cifras históricas (55 pruebas y 64.39 %; la auditoría inicial de este trabajo obtuvo 61 y 60.13 %).
- **Consecuencia:** el lector no puede saber qué ejecución/commit respaldan esas cifras. Las afirmaciones históricas de integración tampoco se revalidaron en este entorno.
- **Recomendación:** fechar resultados con revisión/commit, actualizar cifras al publicar una ejecución nueva y separar claramente pruebas unitarias de pruebas HTTP/SQL externas.

### A-16 — El lote SQL se detenía antes de crear avisos y rechazos en una base nueva

- **Prioridad:** Alto
- **Estado:** Corregido y verificado desde cero. El índice ahora es filtrado sobre columnas físicas, el inicializador consume los resultados restantes del lote y comprueba la presencia de las seis tablas requeridas.
- **Ubicación:** [`backend/sql/create_schema.sql:174`](./backend/sql/create_schema.sql#L174), [`backend/sql/create_schema.sql:199`](./backend/sql/create_schema.sql#L199), [`backend/app/core/database.py:96`](./backend/app/core/database.py#L96).
- **Problema:** SQL Server no admite una columna calculada en el predicado de un índice filtrado. El error no se propagaba y la inicialización parecía terminar aunque no llegara a crear `rechazos_mision` ni `avisos`.
- **Consecuencia:** la primera solicitud de donación podía insertarse y luego responder 500 al guardar el aviso; el resto de rutas que consultaban esas tablas también fallaban.
- **Solución aplicada:** se usa un índice filtrado sobre `entregas.voluntario_id` y `estado`; `initialize_database()` consume resultados pendientes y falla explícitamente si falta alguna tabla.
- **Prueba:** inicialización de una base temporal vacía, tablas e índice comprobados, health check y flujo HTTP completo 22/22.

## Inventario de endpoints HTTP revisados

La lista se obtuvo del OpenAPI de la aplicación importada; esto enumera el contrato, pero no equivale a ejecutar las rutas contra SQL Server.

| Método y ruta | Acceso/regla principal revisada |
|---|---|
| `POST /api/auth/registro` | Público; solo roles negocio, comedor y voluntario. |
| `POST /api/auth/login` | Público. |
| `GET /api/usuarios` | Administrador; filtro opcional por rol. |
| `GET /api/usuarios/me` | Usuario autenticado. |
| `PATCH /api/usuarios/me/disponible` | Voluntario autenticado. |
| `PUT`, `PATCH`, `DELETE /api/usuarios/{usuario_id}` | Administrador. |
| `GET`, `POST /api/donaciones/` | Lectura filtrada por rol; creación por admin/negocio. |
| `GET /api/donaciones/disponibles` | Admin, comedor o voluntario. |
| `PUT`, `DELETE /api/donaciones/{donacion_id}` | Admin o propietario; revisar A-14. |
| `GET`, `POST /api/solicitudes/` | Lectura por rol; creación por admin/comedor. |
| `PUT`, `DELETE /api/solicitudes/{solicitud_id}` | Admin o comedor relacionado; revisar A-03 y A-04. |
| `PATCH /api/solicitudes/{solicitud_id}/estado` | Administrador; cancelación pasa por la transacción del flujo. |
| `POST /api/solicitudes/{solicitud_id}/aprobar` | Negocio propietario; aprobación atómica en repositorio. |
| `POST /api/solicitudes/{solicitud_id}/rechazar` | Negocio propietario; revisar A-06. |
| `GET /api/voluntarios/entregas` | Admin, voluntario propio o comedor relacionado. |
| `GET /api/voluntarios/entregas/abiertas` | Voluntario disponible. |
| `GET /api/voluntarios/avisos` | Usuario autenticado; usa el repositorio de avisos vigente y respondió 200 en integración. |
| `POST /api/voluntarios/entregas/{entrega_id}/aceptar` | Voluntario disponible; revisar A-05. |
| `POST /api/voluntarios/entregas/{entrega_id}/pasar` | Voluntario autenticado. |
| `POST /api/voluntarios/entregas/{entrega_id}/recogido` | Voluntario asignado. |
| `POST /api/voluntarios/entregas/{entrega_id}/entregado` | Comedor propietario; transición a entregada. |
| `POST /api/voluntarios/entregas/{entrega_id}/confirmar` | Comedor propietario; implementa la misma transición que `/entregado`. |
| `PATCH /api/voluntarios/entregas/{entrega_id}/estado` | Admin/voluntario asignado; no permite aceptar sin asignación atómica. |
| `GET /api/entregas/abiertas` | Voluntario disponible, comedor, negocio o admin con filtrado por rol. |
| `GET /api/dashboard/resumen` | Usuario autenticado; resumen filtrado por rol. |
| `GET /api/avisos/` | Avisos del usuario autenticado. |
| `PATCH /api/avisos/{aviso_id}/leer` | Marca leído solo un aviso propio. |
| `GET /api/health/database` | Público; respondió `ok` contra la base temporal de integración. |

La creación de entregas sucede dentro de la aprobación de una solicitud; no hay un CRUD HTTP independiente completo de entregas. Hay dos rutas de confirmación (`/entregado` y `/confirmar`) con comportamiento duplicado.

## SQL Server: esquema y relaciones

Se ejecutó `initialize_database()` en una base temporal recién creada; quedaron
las seis tablas requeridas, claves y restricciones, índice único por solicitud
y un índice filtrado por voluntario activo. Esta prueba detectó y corrigió el
predicado inválido sobre una columna calculada (A-16).

También se aplicó la inicialización de esquema a la base configurada
`alimento_solidario`. Los conteos antes/después permanecieron en 7 usuarios,
5 donaciones, 9 solicitudes, 3 entregas, 0 rechazos y 8 avisos; no había
entregas duplicadas, misiones activas sin voluntario, duplicación de misión por
voluntario, estados legacy, donaciones disponibles vencidas, aprobaciones sin
entrega ni cantidades aprobadas excedidas. No se eliminó ningún registro.

Las claves foráneas verifican existencia, no rol de usuario; la regla de rol se
valida en servicios. No se hicieron escrituras de flujo HTTP en la base
configurada.

## Pruebas y verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| Backend: `backend\.venv\Scripts\python.exe -m pytest -q` | **68 pasaron**; cobertura total **59.49 %**. |
| Frontend: `npm test -- --watch=false` en `Frontend` | **11 archivos, 29 pruebas pasaron**. |
| Frontend: `npm run build` en `Frontend` | **Compilación de producción exitosa**; el artefacto no contiene loopback de API. |
| SQL Server: inicialización desde cero | **Seis tablas creadas**, seed coherente, índice único por solicitud y restricción de misiones activas verificados. |
| SQL Server: base configurada | Esquema actualizado; conteos idénticos antes/después; sin anomalías de relaciones/estados indicadas arriba. |
| HTTP: `scripts.smoke_test` sobre base temporal | **22/22 comprobaciones**; registro/login, donación, solicitud, aprobación, aceptación, recogida, confirmación, avisos, dashboard y permisos por rol. |
| `/api/health/database` y `/api/voluntarios/avisos` | Ambas rutas respondieron **200** contra la base temporal. |
| Clave JWT y contraseñas | Clave local demo rotada; validación de configuración pública y tope bcrypt de 72 bytes cubiertos por pruebas. |

## No verificado y motivo

- **Carreras concurrentes reales (dos aprobaciones/rechazos o dos aceptaciones
  al mismo tiempo):** no se lanzó una prueba de estrés multi-conexión. Hay
  transacciones serializables, actualizaciones condicionales y restricciones
  únicas; su comportamiento concurrente extremo queda pendiente de una prueba
  específica.
- **Cancelación/rechazo HTTP con SQL Server:** la lógica y los casos límite
  tienen pruebas unitarias, pero el smoke HTTP completo ejercitó el camino de
  aprobación y entrega, no cancelación/rechazo de datos.
- **Navegador en sesión autenticada:** no se volvió a recorrer el dashboard ni
  formularios visualmente tras los cambios; se validaron suites y build, no
  consola real del navegador.
- **Despliegue público/proxy same-origin:** se verificó que el build no contiene
  loopback y que la configuración obliga a usar clave y certificado seguros;
  no se configuró un proxy o servidor de producción.
- **Flujos HTTP sobre `alimento_solidario`:** deliberadamente no se ejecutaron
  para no alterar sus registros. La integración completa fue sobre una base
  temporal que se eliminó al terminar; la base del proyecto solo recibió DDL
  no destructivo y se verificó con conteos antes/después.
- **`database_smoke_test.py` por separado:** no se ejecutó contra la base del
  proyecto porque crea y elimina un usuario. La persistencia y el flujo SQL se
  verificaron en la base temporal completa.
