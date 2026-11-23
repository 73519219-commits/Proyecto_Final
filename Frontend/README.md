# AlimentoSolidario Angular

Frontend Angular de AlimentoSolidario Huancayo.

## Inicio

```bash
cd Frontend
npm install
npm start
```

Abre `http://localhost:4200/`. FastAPI debe escuchar en
`http://127.0.0.1:8000`.

En desarrollo, la URL de API se configura en
`src/environments/environment.development.ts`. En producción,
`environment.ts` usa `/api`; el servidor web debe enrutar esa ruta al backend
con un proxy same-origin.

La configuración de entornos está en:

- `src/environments/environment.ts`
- `src/environments/environment.development.ts`

El interceptor añade el token Bearer y `localStorage` conserva la sesión.

## Usuarios demo

| Rol | Correo | Contraseña |
|---|---|---|
| Admin | `admin@alimentosolidario.pe` | `admin123` |
| Negocio | `negocio@panaderia.pe` | `negocio123` |
| Comedor | `comedor@esperanza.pe` | `comedor123` |
| Voluntario | `voluntario@correo.pe` | `voluntario123` |

## Menús por rol

- Negocio: Inicio, Mis donaciones, Solicitudes recibidas, Mi impacto.
- Comedor: Inicio, Mis solicitudes, Por confirmar, Mi impacto.
- Voluntario: Inicio, Mis entregas, Historial, Mi impacto.
- Admin: Inicio, Usuarios, Donaciones, Solicitudes y Voluntarios.

Cada principal consume `/api/dashboard/resumen` y muestra trabajo propio.
Ocultar acciones en Angular no reemplaza la autorización de FastAPI.

## Flujo operativo de 7 pasos

1. El negocio publica una donación.
2. El comedor solicita y elige recoger, trasladar o ambos.
3. El negocio aprueba o rechaza; al aprobar se crea una misión abierta.
4. El voluntario disponible acepta o pasa.
5. La aceptación avisa al comedor y, según el apoyo, al negocio.
6. El voluntario recoge y el comedor confirma la recepción.
7. El admin supervisa y puede intervenir.

Después de aprobar se muestran botones seguros `tel:` y `wa.me`.
La campana carga avisos al entrar y refresca cada 30 segundos.

## Comandos

```bash
npm run build
npm test -- --watch=false
ng test --watch=false
```

## Auditoría técnica — 23 noviembre de 2026

- Compilación de producción Angular: exitosa.
- Suite frontend: 11 archivos y 29 pruebas aprobadas.
- Las rutas protegidas, servicios, interceptores y mapeadores están cubiertos por
  las pruebas existentes.
- Backend y SQL Server: inicialización de esquema probada en una base temporal;
  integración HTTP completa con 22 comprobaciones aprobadas.
- Recomendación operativa: cambiar las cuentas demo antes de desplegar fuera
  de un entorno local.
