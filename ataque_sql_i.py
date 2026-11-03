"""Pruebas HTTP controladas de tres técnicas SQLi en el servidor local."""

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


TIEMPO_ESPERA = 3
MODOS = ("vulnerable", "corregido")
CASOS = (
    ("concatenacion", "control normal", "Ana"),
    ("concatenacion", "OR 1=1", "' OR 1=1 -- "),
    ("union", "control normal", "Ana"),
    (
        "union",
        "UNION cuentas",
        "no-existe' UNION SELECT cuentas.id, usuarios.nombre, 'Cuenta ' || cuentas.numero_cuenta || ' | ' || cuentas.tipo_cuenta || ' | Saldo ' || cuentas.moneda || ' ' || printf('%.2f', cuentas.saldo) || ' | ' || cuentas.estado FROM cuentas JOIN usuarios ON usuarios.id=cuentas.usuario_id -- ",
    ),
    ("booleano", "control normal", "Ana"),
    (
        "booleano",
        "primera letra es A",
        "Ana Torres' AND (SELECT substr(nombre,1,1) FROM usuarios WHERE id=1)='A' -- ",
    ),
    (
        "booleano",
        "primera letra es Z",
        "Ana Torres' AND (SELECT substr(nombre,1,1) FROM usuarios WHERE id=1)='Z' -- ",
    ),
)


def consultar(tipo, nombre, modo, puerto):
    parametros = urlencode({
        "nombre": nombre,
        "modo": modo,
        "tipo": tipo,
        "formato": "json",
    })
    url = f"http://127.0.0.1:{puerto}/buscar?{parametros}"
    try:
        respuesta = urlopen(url, timeout=TIEMPO_ESPERA)
    except HTTPError as error:
        respuesta = error
    with respuesta:
        estado = respuesta.status
        cuerpo = respuesta.read().decode("utf-8", errors="replace")
    try:
        datos = json.loads(cuerpo)
    except json.JSONDecodeError:
        datos = {"respuesta": cuerpo[:300]}
    return estado, datos


def describir_respuesta(tipo, estado, datos):
    if estado != 200 or "error" in datos:
        return f"HTTP {estado}; respuesta={datos}"
    if tipo == "booleano":
        return f"HTTP {estado}; señal coincide={datos.get('coincide')}"
    filas = [
        (registro.get("nombre", "?"), registro.get("dato", ""))
        for registro in datos.get("resultados", [])
    ]
    return f"HTTP {estado}; total={datos.get('total')}; datos={filas}"


def main():
    parser = argparse.ArgumentParser(description="Pruebas SQL Injection al laboratorio local.")
    parser.add_argument("--port", type=int, default=5000, help="Puerto del servidor local (por defecto: 5000).")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port debe estar entre 1 y 65535.")

    print(f"Pruebas SQL Injection: servidor local 127.0.0.1:{args.port}")
    print("Las mismas entradas se envían en modo vulnerable y corregido.\n")
    resultados = {modo: {} for modo in MODOS}
    try:
        for modo in MODOS:
            print(f"Modo: {modo.upper()}")
            for tipo, etiqueta, entrada in CASOS:
                estado, datos = consultar(tipo, entrada, modo, args.port)
                resultados[modo][(tipo, etiqueta)] = (estado, datos)
                print(f"  {tipo} / {etiqueta}: entrada={entrada!r}")
                print(f"    {describir_respuesta(tipo, estado, datos)}")
            print()
    except (URLError, TimeoutError, OSError) as error:
        print(f"No se pudo consultar el servidor local: {error}")
        print(f"Inicia primero el servidor con: python app_vulnerable.py --port {args.port}")
        return 1

    todo_correcto = True
    for tipo in ("concatenacion", "union"):
        control_estado, control = resultados["vulnerable"][(tipo, "control normal")]
        ataque_estado, ataque = resultados["vulnerable"][(tipo, "OR 1=1" if tipo == "concatenacion" else "UNION cuentas")]
        seguro_estado, seguro = resultados["corregido"][(tipo, "OR 1=1" if tipo == "concatenacion" else "UNION cuentas")]
        control_ok = control_estado == 200 and control.get("total") == 1
        if tipo == "concatenacion":
            vulnerable_ok = ataque_estado == 200 and ataque.get("total", 0) > control.get("total", 0)
            corregido_ok = seguro_estado == 200 and seguro.get("total") == 0
        else:
            extraidos = [
                fila.get("dato", "")
                for fila in ataque.get("resultados", [])
                if fila.get("dato", "").startswith("Cuenta ")
                and "Saldo USD" in fila.get("dato", "")
            ]
            vulnerable_ok = ataque_estado == 200 and len(extraidos) == 2
            corregido_ok = seguro_estado == 200 and seguro.get("total") == 0
        modo_ok = control_ok and vulnerable_ok and corregido_ok
        todo_correcto = todo_correcto and modo_ok
        resultado = "APROBADA" if modo_ok else "FALLIDA"
        if tipo == "union":
            detalle = f"UNION obtuvo {len(extraidos)} cuenta(s) con saldo ficticio; corregido devolvió {seguro.get('total')}"
        else:
            detalle = f"vulnerable devolvió {ataque.get('total')}; corregido devolvió {seguro.get('total')}"
        print(f"Verificación {tipo}: control normal {'correcto' if control_ok else 'incorrecto'}; {detalle}; {resultado}.")

    verdadero_v, resp_verdadero_v = resultados["vulnerable"][("booleano", "primera letra es A")]
    falso_v, resp_falso_v = resultados["vulnerable"][("booleano", "primera letra es Z")]
    verdadero_s, resp_verdadero_s = resultados["corregido"][("booleano", "primera letra es A")]
    falso_s, resp_falso_s = resultados["corregido"][("booleano", "primera letra es Z")]
    control_v, resp_control_v = resultados["vulnerable"][("booleano", "control normal")]
    control_s, resp_control_s = resultados["corregido"][("booleano", "control normal")]
    booleano_ok = (
        control_v == control_s == verdadero_v == falso_v == verdadero_s == falso_s == 200
        and resp_control_v.get("coincide") is True
        and resp_control_s.get("coincide") is True
        and resp_verdadero_v.get("coincide") is True
        and resp_falso_v.get("coincide") is False
        and resp_verdadero_s.get("coincide") is False
        and resp_falso_s.get("coincide") is False
    )
    todo_correcto = todo_correcto and booleano_ok
    print(
        "Verificación booleano: la señal revela que la inicial ficticia es A; "
        "corregido no acepta la condición como SQL; "
        f"{'APROBADA' if booleano_ok else 'FALLIDA'}."
    )
    print("Resultado general: " + ("TODAS LAS PRUEBAS APROBADAS" if todo_correcto else "HAY PRUEBAS FALLIDAS"))
    return 0 if todo_correcto else 1


if __name__ == "__main__":
    raise SystemExit(main())
