"""Consultas SQL para crear y poblar la tabla cuentas."""

cuentas = """
CREATE TABLE IF NOT EXISTS cuentas (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    numero_cuenta TEXT NOT NULL UNIQUE,
    tipo_cuenta TEXT NOT NULL,
    saldo NUMERIC NOT NULL CHECK (saldo >= 0),
    moneda TEXT NOT NULL,
    estado TEXT NOT NULL,
    fecha_apertura TEXT NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
"""

insertar_cuentas = """
INSERT INTO cuentas (
    usuario_id, numero_cuenta, tipo_cuenta, saldo, moneda, estado, fecha_apertura
) VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(numero_cuenta) DO NOTHING
"""
