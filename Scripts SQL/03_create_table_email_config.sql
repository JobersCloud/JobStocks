-- ============================================
-- Tabla: email_config
-- Descripción: Configuración SMTP para envío de emails
-- Base de datos: ApiRestStocks
-- ============================================

USE ApiRestStocks;
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[email_config](
    [id] [int] IDENTITY(1,1) NOT NULL,
    [nombre_configuracion] [varchar](100) NOT NULL,
    [smtp_server] [varchar](200) NOT NULL,
    [smtp_port] [int] NOT NULL,
    [email_from] [varchar](200) NOT NULL,
    [email_password] [varchar](500) NOT NULL,
    [email_to] [varchar](200) NOT NULL,
    [activo] [bit] NOT NULL,
    [fecha_creacion] [datetime] NOT NULL,
    [fecha_modificacion] [datetime] NULL,

    CONSTRAINT [PK_email_config] PRIMARY KEY CLUSTERED ([id] ASC)
        WITH (
            PAD_INDEX = OFF,
            STATISTICS_NORECOMPUTE = OFF,
            IGNORE_DUP_KEY = OFF,
            ALLOW_ROW_LOCKS = ON,
            ALLOW_PAGE_LOCKS = ON
        ) ON [PRIMARY]
) ON [PRIMARY];
GO

-- Valores por defecto
ALTER TABLE [dbo].[email_config] ADD DEFAULT ((1)) FOR [activo];
GO

ALTER TABLE [dbo].[email_config] ADD DEFAULT (GETDATE()) FOR [fecha_creacion];
GO

PRINT 'Tabla email_config creada exitosamente';
