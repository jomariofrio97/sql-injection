"""Laboratorio local de SQL Injection. No usar en producción."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from consultas.buscar_usuarios import (
    buscar_usuarios_concatenada,
    buscar_usuarios_parametrizada,
)
from consultas.cuentas import cuentas, insertar_cuentas
from consultas.limpieza import eliminar_datos_adicionales_demo
from consultas.usuarios import insertar_usuarios, usuarios


app = Flask(__name__)
RUTA_BD = Path(__file__).resolve().parent / "mi_base.db"
MODOS = {"vulnerable", "corregido"}
TIPOS = {"concatenacion", "union", "booleano"}

def inicializar_bd():
    """Crea las tablas y añade registros ficticios sin duplicarlos."""
    with closing(sqlite3.connect(RUTA_BD, timeout=3)) as conexion:
        with conexion:
            conexion.execute(usuarios)
            conexion.executemany(insertar_usuarios, [
                ("Ana Torres", "ana@example.com"),
                ("Luis García", "luis@example.com"),
                ("María López", "maria@example.com"),
                ("Carlos Ruiz", "carlos@example.com"),
            ])
            conexion.execute(cuentas)
            conexion.executemany(insertar_cuentas, [
                (1, "210045006781", "Ahorros", 1245.75, "USD", "Activa", "2021-06-14"),
                (2, "210045009342", "Corriente", 3840.20, "USD", "Activa", "2022-09-02"),
            ])
            # Elimina la tabla de ejemplo con filas genéricas creada por la versión anterior.
            conexion.execute(eliminar_datos_adicionales_demo)


def buscar_registros(nombre, modo):
    """Ejecuta la búsqueda del laboratorio en el modo elegido."""
    with closing(sqlite3.connect(RUTA_BD, timeout=3)) as conexion:
        conexion.row_factory = sqlite3.Row
        if modo == "vulnerable":
            # VULNERABILIDAD INTENCIONAL: entrada concatenada a la consulta.
            # Solo para la demostración local con datos ficticios.
            consulta = buscar_usuarios_concatenada.format(nombre=nombre)
            filas = conexion.execute(consulta).fetchall()
        else:
            # La entrada se envía como parámetro y no puede modificar la consulta.
            filas = conexion.execute(
                buscar_usuarios_parametrizada,
                (f"%{nombre}%",),
            ).fetchall()
        return [dict(fila) for fila in filas]


@app.get("/")
def inicio():
    modo = request.args.get("modo", "vulnerable")
    tipo = request.args.get("tipo", "concatenacion")
    if modo not in MODOS:
        modo = "vulnerable"
    if tipo not in TIPOS:
        tipo = "concatenacion"
    return render_template(
        "index.html",
        modo=modo,
        tipo=tipo,
        filtro="",
        registros=[],
        coincide=False,
        se_busco=False,
    )


@app.get("/buscar")
def buscar_usuario():
    nombre = request.args.get("nombre", "")
    modo = request.args.get("modo", "vulnerable")
    tipo = request.args.get("tipo", "concatenacion")
    if modo not in MODOS:
        return jsonify({"error": "El modo debe ser vulnerable o corregido."}), 400
    if tipo not in TIPOS:
        return jsonify({"error": "El tipo debe ser concatenacion, union o booleano."}), 400

    registros = buscar_registros(nombre, modo)
    coincide = bool(registros)
    if request.args.get("formato") == "json":
        respuesta = {"modo": modo, "tipo": tipo, "entrada": nombre}
        if tipo == "booleano":
            respuesta.update({
                "coincide": coincide,
                "mensaje": "Hay coincidencia." if coincide else "No hay coincidencia.",
            })
        else:
            respuesta.update({"total": len(registros), "resultados": registros})
        return jsonify(respuesta)

    return render_template(
        "index.html",
        modo=modo,
        tipo=tipo,
        filtro=nombre,
        registros=registros,
        coincide=coincide,
        se_busco=True,
    )


inicializar_bd()


if __name__ == "__main__":
    # Loopback limita el servidor al ambiente local.
    parser = argparse.ArgumentParser(description="Servidor local del laboratorio SQL Injection.")
    parser.add_argument("--port", type=int, default=5000, help="Puerto local (por defecto: 5000).")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port debe estar entre 1 y 65535.")
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
