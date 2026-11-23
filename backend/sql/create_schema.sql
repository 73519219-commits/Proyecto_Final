IF OBJECT_ID(N'dbo.usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_usuarios PRIMARY KEY,
        nombres NVARCHAR(100) NOT NULL,
        apellidos NVARCHAR(100) NOT NULL,
        correo NVARCHAR(320) NOT NULL,
        password_hash NVARCHAR(255) NOT NULL,
        telefono NVARCHAR(30) NOT NULL,
        direccion NVARCHAR(250) NOT NULL,
        rol NVARCHAR(20) NOT NULL,
        disponible BIT NOT NULL CONSTRAINT DF_usuarios_disponible DEFAULT 0,
        estado NVARCHAR(20) NOT NULL
            CONSTRAINT DF_usuarios_estado DEFAULT N'activo',
        CONSTRAINT UQ_usuarios_correo UNIQUE (correo),
        CONSTRAINT CK_usuarios_rol CHECK
            (rol IN (N'admin', N'negocio', N'comedor', N'voluntario')),
        CONSTRAINT CK_usuarios_estado CHECK
            (estado IN (N'activo', N'inactivo'))
    );
END;

IF OBJECT_ID(N'dbo.donaciones', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.donaciones (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_donaciones PRIMARY KEY,
        nombre_alimento NVARCHAR(150) NOT NULL,
        descripcion NVARCHAR(500) NOT NULL,
        cantidad INT NOT NULL,
        unidad NVARCHAR(50) NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        direccion_recojo NVARCHAR(250) NOT NULL,
        hora_disponible NVARCHAR(100) NOT NULL,
        estado NVARCHAR(20) NOT NULL
            CONSTRAINT DF_donaciones_estado DEFAULT N'disponible',
        usuario_negocio_id INT NOT NULL,
        CONSTRAINT CK_donaciones_cantidad CHECK (cantidad > 0),
        CONSTRAINT CK_donaciones_estado CHECK
            (estado IN (N'disponible', N'reservada', N'cancelada', N'entregada')),
        CONSTRAINT FK_donaciones_usuarios FOREIGN KEY (usuario_negocio_id)
            REFERENCES dbo.usuarios (id)
    );
END;

IF OBJECT_ID(N'dbo.solicitudes', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.solicitudes (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_solicitudes PRIMARY KEY,
        donacion_id INT NOT NULL,
        comedor_id INT NOT NULL,
        cantidad_solicitada INT NOT NULL,
        tipo_apoyo NVARCHAR(20) NOT NULL CONSTRAINT DF_solicitudes_tipo_apoyo DEFAULT N'ambos',
        necesita_apoyo NVARCHAR(20) NOT NULL CONSTRAINT DF_solicitudes_necesita_apoyo DEFAULT N'ambos',
        estado NVARCHAR(20) NOT NULL
            CONSTRAINT DF_solicitudes_estado DEFAULT N'pendiente',
        CONSTRAINT CK_solicitudes_cantidad CHECK (cantidad_solicitada > 0),
        CONSTRAINT CK_solicitudes_estado CHECK
            (estado IN (N'pendiente', N'aprobada', N'rechazada', N'cancelada')),
        CONSTRAINT FK_solicitudes_donaciones FOREIGN KEY (donacion_id)
            REFERENCES dbo.donaciones (id),
        CONSTRAINT FK_solicitudes_usuarios FOREIGN KEY (comedor_id)
            REFERENCES dbo.usuarios (id)
    );
END;

IF COL_LENGTH(N'dbo.usuarios', N'disponible') IS NULL
BEGIN
    ALTER TABLE dbo.usuarios ADD disponible BIT NOT NULL
        CONSTRAINT DF_usuarios_disponible DEFAULT 0;
END;

IF COL_LENGTH(N'dbo.solicitudes', N'tipo_apoyo') IS NULL
BEGIN
    ALTER TABLE dbo.solicitudes ADD tipo_apoyo NVARCHAR(20) NOT NULL
        CONSTRAINT DF_solicitudes_tipo_apoyo DEFAULT N'ambos';
END;

IF COL_LENGTH(N'dbo.solicitudes', N'necesita_apoyo') IS NULL
BEGIN
    ALTER TABLE dbo.solicitudes ADD necesita_apoyo NVARCHAR(20) NOT NULL
        CONSTRAINT DF_solicitudes_necesita_apoyo DEFAULT N'ambos';
END;

IF OBJECT_ID(N'dbo.entregas', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.entregas (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_entregas PRIMARY KEY,
        solicitud_id INT NOT NULL,
        voluntario_id INT NULL,
        fecha_asignacion DATE NOT NULL,
        fecha_entrega DATE NULL,
        estado NVARCHAR(20) NOT NULL
            CONSTRAINT DF_entregas_estado DEFAULT N'abierta',
        observaciones NVARCHAR(300) NULL,
        tipo_apoyo NVARCHAR(20) NOT NULL CONSTRAINT DF_entregas_tipo_apoyo DEFAULT N'ambos',
        tipo NVARCHAR(20) NOT NULL CONSTRAINT DF_entregas_tipo DEFAULT N'ambos',
        CONSTRAINT CK_entregas_estado CHECK
            (estado IN (N'abierta', N'aceptada', N'recogida', N'entregada', N'cancelada',
                        N'pendiente', N'asignada', N'en_ruta', N'recogido', N'entregado')),
        CONSTRAINT FK_entregas_solicitudes FOREIGN KEY (solicitud_id)
            REFERENCES dbo.solicitudes (id),
        CONSTRAINT FK_entregas_usuarios FOREIGN KEY (voluntario_id)
            REFERENCES dbo.usuarios (id)
    );
END;

IF COL_LENGTH(N'dbo.entregas', N'tipo_apoyo') IS NULL
BEGIN
    ALTER TABLE dbo.entregas ADD tipo_apoyo NVARCHAR(20) NOT NULL
        CONSTRAINT DF_entregas_tipo_apoyo DEFAULT N'ambos';
END;

IF COL_LENGTH(N'dbo.entregas', N'tipo') IS NULL
BEGIN
    ALTER TABLE dbo.entregas ADD tipo NVARCHAR(20) NOT NULL
        CONSTRAINT DF_entregas_tipo DEFAULT N'ambos';
END;

IF EXISTS (
    SELECT solicitud_id
    FROM dbo.entregas
    GROUP BY solicitud_id
    HAVING COUNT(*) > 1
)
BEGIN
    ;THROW 51000, N'Hay varias entregas por solicitud. Revise y resuelva los duplicados antes de aplicar el índice único.', 1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UQ_entregas_solicitud'
      AND object_id = OBJECT_ID(N'dbo.entregas')
)
BEGIN
    CREATE UNIQUE INDEX UQ_entregas_solicitud
    ON dbo.entregas(solicitud_id);
END;

IF EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_entregas_estado' AND parent_object_id = OBJECT_ID(N'dbo.entregas')
)
    ALTER TABLE dbo.entregas DROP CONSTRAINT CK_entregas_estado;

UPDATE dbo.entregas SET estado = N'abierta' WHERE estado = N'pendiente';
UPDATE dbo.entregas SET estado = N'aceptada' WHERE estado IN (N'asignada', N'en_ruta');
UPDATE dbo.entregas SET estado = N'recogida' WHERE estado IN (N'recogido', N'entregado');

ALTER TABLE dbo.entregas WITH CHECK ADD CONSTRAINT CK_entregas_estado CHECK
    (estado IN (N'abierta', N'aceptada', N'recogida', N'entregada', N'cancelada'));

IF EXISTS (
    SELECT voluntario_id
    FROM dbo.entregas
    WHERE estado IN (N'aceptada', N'recogida') AND voluntario_id IS NULL
)
BEGIN
    ;THROW 51001, N'Hay entregas activas sin voluntario asignado. Resuelva esos registros antes de continuar.', 1;
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE name = N'CK_entregas_activa_voluntario'
      AND parent_object_id = OBJECT_ID(N'dbo.entregas')
)
BEGIN
    ALTER TABLE dbo.entregas WITH CHECK ADD CONSTRAINT CK_entregas_activa_voluntario
        CHECK (estado NOT IN (N'aceptada', N'recogida') OR voluntario_id IS NOT NULL);
END;

IF EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UQ_entregas_voluntario_activo'
      AND object_id = OBJECT_ID(N'dbo.entregas')
)
    DROP INDEX UQ_entregas_voluntario_activo ON dbo.entregas;

IF COL_LENGTH(N'dbo.entregas', N'voluntario_activo_id') IS NOT NULL
    ALTER TABLE dbo.entregas DROP COLUMN voluntario_activo_id;

IF EXISTS (
    SELECT voluntario_id
    FROM dbo.entregas
    WHERE estado IN (N'aceptada', N'recogida') AND voluntario_id IS NOT NULL
    GROUP BY voluntario_id
    HAVING COUNT(*) > 1
)
BEGIN
    ;THROW 51002, N'Hay voluntarios con varias entregas activas. Revise esos registros antes de aplicar el índice único.', 1;
END;

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = N'UQ_entregas_voluntario_activo'
      AND object_id = OBJECT_ID(N'dbo.entregas')
)
BEGIN
    CREATE UNIQUE INDEX UQ_entregas_voluntario_activo
        ON dbo.entregas (voluntario_id)
        WHERE estado IN (N'aceptada', N'recogida')
          AND voluntario_id IS NOT NULL;
END;

IF OBJECT_ID(N'dbo.rechazos_mision', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.rechazos_mision (
        entrega_id INT NOT NULL,
        voluntario_id INT NOT NULL,
        creado_en DATETIME2 NOT NULL CONSTRAINT DF_rechazos_mision_creado DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_rechazos_mision PRIMARY KEY (entrega_id, voluntario_id),
        CONSTRAINT FK_rechazos_entrega FOREIGN KEY (entrega_id) REFERENCES dbo.entregas (id),
        CONSTRAINT FK_rechazos_voluntario FOREIGN KEY (voluntario_id) REFERENCES dbo.usuarios (id)
    );
END;

IF OBJECT_ID(N'dbo.avisos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.avisos (
        id INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_avisos PRIMARY KEY,
        usuario_destino INT NOT NULL,
        tipo NVARCHAR(50) NOT NULL,
        mensaje NVARCHAR(500) NOT NULL,
        referencia_id INT NULL,
        leido BIT NOT NULL CONSTRAINT DF_avisos_leido DEFAULT 0,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_avisos_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_avisos_usuario FOREIGN KEY (usuario_destino) REFERENCES dbo.usuarios (id)
    );
END;

IF COL_LENGTH(N'dbo.avisos', N'usuario_destino') IS NULL
BEGIN
    ALTER TABLE dbo.avisos ADD usuario_destino INT NULL;
    IF COL_LENGTH(N'dbo.avisos', N'usuario_id') IS NOT NULL
        EXEC(N'UPDATE dbo.avisos SET usuario_destino = usuario_id');
END;

IF COL_LENGTH(N'dbo.avisos', N'tipo') IS NULL
BEGIN
    ALTER TABLE dbo.avisos ADD tipo NVARCHAR(50) NOT NULL
        CONSTRAINT DF_avisos_tipo DEFAULT N'sistema';
END;

IF COL_LENGTH(N'dbo.avisos', N'referencia_id') IS NULL
BEGIN
    ALTER TABLE dbo.avisos ADD referencia_id INT NULL;
    IF COL_LENGTH(N'dbo.avisos', N'entrega_id') IS NOT NULL
        EXEC(N'UPDATE dbo.avisos SET referencia_id = entrega_id');
END;

IF COL_LENGTH(N'dbo.avisos', N'created_at') IS NULL
BEGIN
    ALTER TABLE dbo.avisos ADD created_at DATETIME2 NOT NULL
        CONSTRAINT DF_avisos_created DEFAULT SYSUTCDATETIME();
    IF COL_LENGTH(N'dbo.avisos', N'creado_en') IS NOT NULL
        EXEC(N'UPDATE dbo.avisos SET created_at = creado_en');
END;
