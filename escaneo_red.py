"""Escáner TCP elemental limitado a direcciones de loopback."""

import argparse
import ipaddress
import socket


SERVICIOS_PROBABLES = {
    22: "SSH (probable)",
    80: "HTTP (probable)",
    443: "HTTPS (probable)",
    5000: "servidor HTTP de desarrollo, como Flask (probable)",
    8080: "HTTP alternativo (probable)",
}


def servicio_asociado(puerto):
    """Devuelve una asociación convencional del puerto, no una detección."""
    if puerto in SERVICIOS_PROBABLES:
        return SERVICIOS_PROBABLES[puerto]
    try:
        return f"{socket.getservbyport(puerto, 'tcp')} (asociado al número de puerto)"
    except OSError:
        return "sin nombre de servicio asociado conocido"


def comprobar_puerto(host, puerto, timeout):
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return "ABIERTO"
    except ConnectionRefusedError:
        return "CERRADO (conexión rechazada)"
    except (socket.timeout, TimeoutError):
        return "SIN RESPUESTA (tiempo agotado)"
    except OSError as error:
        return f"ERROR DE CONEXIÓN ({error})"


def main():
    parser = argparse.ArgumentParser(
        description="Comprobación TCP básica de puertos en localhost."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="IP de loopback (por defecto: 127.0.0.1); no se aceptan hosts externos.",
    )
    parser.add_argument(
        "--puertos",
        type=int,
        nargs="+",
        default=[80, 443, 5000, 8080],
        help="Puertos TCP que se comprobarán (por defecto: 80 443 5000 8080).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.5,
        help="Tiempo máximo de conexión por puerto en segundos (por defecto: 0.5).",
    )
    args = parser.parse_args()

    try:
        objetivo = ipaddress.ip_address(args.host)
    except ValueError:
        parser.error("--host debe ser una dirección IP de loopback válida.")
    if not objetivo.is_loopback:
        parser.error("Este laboratorio solo permite analizar localhost/loopback.")
    if not args.puertos or len(args.puertos) > 32:
        parser.error("Indica entre 1 y 32 puertos.")
    if any(puerto < 1 or puerto > 65535 for puerto in args.puertos):
        parser.error("Los puertos deben estar entre 1 y 65535.")
    if not 0.05 <= args.timeout <= 10:
        parser.error("--timeout debe estar entre 0.05 y 10 segundos.")

    puertos = sorted(set(args.puertos))
    print(f"Host analizado: {objetivo}")
    print(f"Puertos TCP comprobados: {', '.join(map(str, puertos))}")
    print("Resultados:")
    for puerto in puertos:
        estado = comprobar_puerto(str(objetivo), puerto, args.timeout)
        servicio = servicio_asociado(puerto)
        print(f"  TCP/{puerto}: {estado}; servicio asociado/probable: {servicio}")


if __name__ == "__main__":
    main()
