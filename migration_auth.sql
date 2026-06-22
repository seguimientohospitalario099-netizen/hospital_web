-- ============================================================
-- MIGRACIÓN DE SEGURIDAD Y AUDITORÍA
-- Ejecutar este script en el Editor SQL de Supabase
-- ============================================================

-- 1. Añadir columna 'email' a la tabla 'usuarios'
ALTER TABLE "usuarios" ADD COLUMN IF NOT EXISTS "email" TEXT UNIQUE;

-- 2. Crear tabla 'actividades_hospital' para logs de auditoría
CREATE TABLE IF NOT EXISTS "actividades_hospital" (
    "id"           SERIAL PRIMARY KEY,
    "usuario"      TEXT NOT NULL,
    "rol"          TEXT NOT NULL,
    "accion"       TEXT NOT NULL,
    "detalles"     TEXT,
    "fecha"        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Habilitar RLS en la nueva tabla
ALTER TABLE "actividades_hospital" ENABLE ROW LEVEL SECURITY;

-- 4. Crear política de acceso total para service_role (usado por el backend)
DROP POLICY IF EXISTS "service_role full access - actividades" ON "actividades_hospital";
CREATE POLICY "service_role full access - actividades"
    ON "actividades_hospital" FOR ALL USING (true);
