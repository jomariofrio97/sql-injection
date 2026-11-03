"""Consultas SQL para crear y poblar la tabla usuarios."""

usuarios = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

insertar_usuarios = """
INSERT INTO usuarios (nombre, correo)
VALUES (?, ?)
ON CONFLICT(correo) DO NOTHING
"""
