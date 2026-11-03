# Laboratorio de SQL Injection

Práctica académica local para observar una inyección SQL real en una aplicación
Flask con SQLite y comprobar cómo las consultas parametrizadas evitan que la
entrada modifique la consulta. La base usa registros ficticios.

## Tecnologías y componentes

- **Python, Flask y SQLite:** servidor web local, formulario de búsqueda y base
  de datos creada automáticamente en `mi_base.db`.
- **`app_vulnerable.py`:** rutas de la aplicación y lógica de base de datos.
  La interfaz HTML está en `templates/index.html` y los estilos en
  `static/css/estilos.css`. La página mantiene un campo de búsqueda y los modos
  **Vulnerable** y **Corregido**. En el mismo campo se ingresan las pruebas de
  entrada concatenada, `UNION-based` y `Boolean blind`.
- **`consultas/`:** contiene las consultas SQL organizadas por tabla y
  operación. `consultas/buscar_usuarios.py` guarda la versión concatenada para
  la demostración vulnerable y la versión parametrizada para el modo corregido.
  Las tablas `usuarios` y `cuentas` usan datos ficticios con formato realista.
- **`ataque_sql_i.py`:** envía por HTTP controles y payloads para las tres
  técnicas a `127.0.0.1`, en ambos modos, y compara las respuestas reales.
- **`escaneo_red.py`:** comprueba puertos TCP en direcciones de loopback y
  muestra si están abiertos, rechazados o sin respuesta, con el servicio
  asociado/probable al número del puerto cuando se conoce.
- **`MANUAL_USO.md`:** comandos de PowerShell para instalar, ejecutar y repetir
  la práctica, además de la explicación de seguridad de SQLite.

## Cómo se relacionan

La búsqueda concatenada muestra cómo una entrada cambia la condición SQL;
`UNION-based` recupera filas adicionales ficticias de otra tabla y `Boolean
blind` permite inferir una condición a partir de una señal de coincidencia sin
devolver las filas. El modo corregido parametriza la búsqueda y bloquea esos
efectos. El escáner comprueba que el servidor local, normalmente en TCP/5000,
está accesible.

## Inicio rápido en Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask
.\.venv\Scripts\python.exe .\app_vulnerable.py
```

Con el servidor en ejecución, abre otra terminal en esta carpeta y ejecuta:

```powershell
.\.venv\Scripts\python.exe .\ataque_sql_i.py
.\.venv\Scripts\python.exe .\escaneo_red.py --host 127.0.0.1 --puertos 5000 8080
```

La guía completa está en [MANUAL_USO.md](MANUAL_USO.md).

## Seguridad y uso

Este repositorio contiene código **intencionalmente vulnerable** para una
práctica controlada. El servidor escucha solo en `127.0.0.1`, tiene el modo de
depuración desactivado y no publica una ruta para descargar la base. El modo
corregido usa consultas parametrizadas. `mi_base.db` y sus archivos auxiliares
se excluyen de Git; las filas son ficticias. La aplicación no configura ACL
del sistema operativo: el acceso local al archivo depende de los permisos de
Windows de la carpeta. SQLite no implementa cuentas ni roles de usuarios.

Usa el proyecto únicamente en el laboratorio local; no lo conectes a datos
reales ni lo despliegues en Internet. El escáner rechaza direcciones que no
sean de loopback.
