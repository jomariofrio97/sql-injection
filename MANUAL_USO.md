# Manual reproducible: laboratorio de SQL Injection

Sigue estos pasos desde **Windows PowerShell**, en la carpeta del repositorio.
El laboratorio usa `127.0.0.1`, registros ficticios y no está pensado para
Internet ni para datos reales.

## 1. Preparar Python y Flask

Se requiere Python 3.9 o superior. Comprueba Python y crea un entorno virtual:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask
```

Los comandos siguientes usan el Python de ese entorno. La aplicación y los
scripts usan `sqlite3`, `socket`, `urllib` y otros módulos de la biblioteca
estándar; Flask es la única dependencia externa.

## 2. Crear o preparar la base SQLite

No se necesita crear la base a mano. Al iniciar `app_vulnerable.py`, se crea
`mi_base.db` en la carpeta del proyecto si no existe y se preparan dos tablas.
Las consultas SQL de inicialización están separadas por tabla en
`consultas/usuarios.py` y `consultas/cuentas.py`; la limpieza de una tabla de
prácticas anterior está en `consultas/limpieza.py`. `app_vulnerable.py` importa
esas variables y las pasa a `conexion.execute` o `executemany`.
Las consultas de búsqueda también están separadas en
`consultas/buscar_usuarios.py`: la variable `buscar_usuarios_concatenada` se
usa en modo Vulnerable y `buscar_usuarios_parametrizada` en modo Corregido.
`usuarios` contiene cuatro clientes ficticios (`@example.com`) y `cuentas`
contiene dos cuentas de ejemplo relacionadas por `usuario_id`. Sus números,
saldos, tipos y estados tienen formato realista, pero son datos inventados
para la práctica. La inicialización no duplica correos ni números de cuenta.
Por ejemplo, una cuenta de Ana aparece así:
`210045006781 | Ahorros | USD 1245.75 | Activa`.
El resultado UNION deja visible ese dato financiero.
Si `mi_base.db` proviene de la versión anterior del laboratorio, al iniciar se
retira la tabla que contenía las filas genéricas y se prepara `cuentas`.

El archivo de la base de datos está excluido de Git. Para revisar localmente
los nombres almacenados:

```powershell
python -c "import sqlite3; c=sqlite3.connect('mi_base.db'); print(c.execute('SELECT nombre, correo FROM usuarios ORDER BY id').fetchall()); c.close()"
```

La salida inicial esperada son las cuatro filas ficticias de `usuarios`.

## 3. Ejecutar la aplicación

En una primera ventana de PowerShell:

```powershell
.\.venv\Scripts\python.exe .\app_vulnerable.py
```

Si creaste el entorno virtual con otro nombre, sustituye `.venv` en los
comandos por ese nombre.

El servidor indica que escucha en `http://127.0.0.1:5000`. Mantén esta ventana
abierta. Abre esa dirección en el navegador: la página muestra el título, la
advertencia y el formulario de búsqueda con el campo de entrada y el modo. El
HTML está en `templates/index.html` y sus estilos en `static/css/estilos.css`;
`app_vulnerable.py` carga la plantilla con Flask.

Si TCP/5000 ya está ocupado, puedes iniciar el mismo servidor en otro puerto,
por ejemplo 5001:

```powershell
.\.venv\Scripts\python.exe .\app_vulnerable.py --port 5001
```

En ese caso abre `http://127.0.0.1:5001/` en el navegador.

Para probar una operación legítima en el navegador, escribe `Ana`, elige
**Vulnerable** o **Corregido** y pulsa **Buscar**. Ambos modos deben mostrar a
Ana Torres. También puedes abrir estas direcciones:

- `http://127.0.0.1:5000/buscar?nombre=Ana&modo=vulnerable`
- `http://127.0.0.1:5000/buscar?nombre=Ana&modo=corregido`

La respuesta web muestra el modo seleccionado y los registros que SQLite
realmente devolvió. La ruta `/buscar` también ofrece JSON si se añade
`&formato=json`; el script de pruebas usa esa respuesta.

## 4. Demostrar la vulnerabilidad y repetir la prueba corregida

Con el servidor todavía en ejecución, abre una segunda ventana en la misma
carpeta y ejecuta:

```powershell
.\.venv\Scripts\python.exe .\ataque_sql_i.py
```

Para el ejemplo alternativo en TCP/5001, ejecuta el mismo cliente con
`--port 5001`:

```powershell
.\.venv\Scripts\python.exe .\ataque_sql_i.py --port 5001
```

El script envía por HTTP controles y payloads para tres técnicas a ambos
modos:

**Nota:** la concatenación insegura es el defecto que permite alterar la
consulta. `UNION-based` y `Boolean blind` son técnicas distintas para explotar
ese defecto; no son mecanismos de base de datos diferentes.

1. **Entrada concatenada:** `' OR 1=1 -- ` amplía la búsqueda de control de 1 a
   4 usuarios en modo vulnerable.
2. **UNION-based:** pega esta entrada en el mismo campo de búsqueda. Combina
   la búsqueda vacía con una consulta a `cuentas` y `usuarios`:

   ```text
   no-existe' UNION SELECT cuentas.id, usuarios.nombre, 'Cuenta ' || cuentas.numero_cuenta || ' | ' || cuentas.tipo_cuenta || ' | Saldo ' || cuentas.moneda || ' ' || printf('%.2f', cuentas.saldo) || ' | ' || cuentas.estado FROM cuentas JOIN usuarios ON usuarios.id=cuentas.usuario_id --
   ```

   En modo vulnerable muestra dos titulares con número de cuenta, tipo, saldo
   y estado. El `SELECT` inyectado devuelve tres columnas, como la consulta
   original.
3. **Boolean blind:** las dos condiciones consultan si la primera letra del
   nombre ficticio con `id=1` es `A` o `Z`:

   ```text
   Ana Torres' AND (SELECT substr(nombre,1,1) FROM usuarios WHERE id=1)='A' --
   Ana Torres' AND (SELECT substr(nombre,1,1) FROM usuarios WHERE id=1)='Z' --
   ```

   En vulnerable, la respuesta solo muestra “hay coincidencia” para `A` y “no
   hay coincidencia” para `Z`; no devuelve las filas. Esa diferencia permite
   inferir el dato carácter a carácter. Escribe un espacio al final de cada
   payload, después de `--`, para terminar el comentario SQL.

Luego repite las mismas entradas en modo corregido. Las entradas se tratan como
texto literal y no producen esos efectos. En cada petición, el script imprime
el código HTTP y la respuesta real relevante. Termina con código `0` si las
expectativas se cumplen y `1` si alguna prueba falla.

En el formulario web, pega cualquiera de estas entradas en el mismo campo de
búsqueda y selecciona **Vulnerable** o **Corregido**. La entrada determina el
efecto SQL; no hay un selector separado para la técnica. El script demuestra
también la señal verdadero/falso de Boolean blind sin mostrar los registros.
No hace falta reiniciar el servidor.

## 5. Escanear los puertos locales

Con Flask todavía activo, ejecuta desde otra terminal:

```powershell
.\.venv\Scripts\python.exe .\escaneo_red.py --host 127.0.0.1 --puertos 5000 8080
```

Si iniciaste Flask en TCP/5001, incluye ese puerto en la comprobación:

```powershell
.\.venv\Scripts\python.exe .\escaneo_red.py --host 127.0.0.1 --puertos 5001 8080
```

El script muestra el host, los puertos comprobados y el resultado individual.
Con la aplicación activa, TCP/5000 debe ser `ABIERTO`; TCP/8080 depende de si
otro servicio local está escuchando. `CERRADO (conexión rechazada)` significa
que el destino rechazó la conexión. `SIN RESPUESTA` significa que venció el
tiempo de espera, por lo que no permite distinguir por sí solo entre filtrado
y otras causas. Los nombres de servicio se asocian al número del puerto y no
son una identificación confirmada del proceso.

El escáner acepta solo direcciones IP de loopback. Si se intenta otra dirección,
el programa la rechaza. Para revisar sus puertos predeterminados (80, 443, 5000
y 8080):

```powershell
.\.venv\Scripts\python.exe .\escaneo_red.py
```

## 6. Protección de SQLite y alcance de los controles

Controles que implementa el proyecto:

- La base se guarda junto a la aplicación; no hay una ruta HTTP que entregue el
  archivo SQLite ni sus tablas.
- Flask escucha exclusivamente en `127.0.0.1`, con `debug=False` y sin
  recargador de desarrollo.
- Los datos de `usuarios` y `cuentas` son ficticios. `mi_base.db`,
  `*.db`, `*.sqlite3` y archivos WAL/SHM
  están excluidos del repositorio para que la base local no se publique por
  accidente.
- En modo **Corregido**, las búsquedas separan el SQL de los valores con `?`.
  Es el control efectivo contra la inyección SQL en estas operaciones.

Controles del sistema operativo:

- SQLite es un archivo local; no tiene cuentas, roles ni permisos propios como
  un servidor gestor de bases de datos. Los usuarios y procesos locales pueden
  leer el archivo según las ACL de Windows de la carpeta. La aplicación no
  cambia esas ACL ni garantiza cifrado del archivo.
- Para inspeccionar los permisos actuales después de crear la base:

  ```powershell
  icacls .\mi_base.db
  ```

- Si el equipo requiere restringir el archivo a la cuenta que ejecuta el
  laboratorio, se puede quitar la herencia y conceder control total a esa
  cuenta (sustituye el valor de `$identidad` si ejecutas el servidor con otra):

  ```powershell
  $identidad = "$env:USERDOMAIN\$env:USERNAME"
  icacls .\mi_base.db /inheritance:r /grant:r "$($identidad):(F)"
  ```

  Para volver a heredar los permisos de la carpeta:

  ```powershell
  icacls .\mi_base.db /reset
  ```

Estos comandos de ACL son una configuración local de Windows, no una función
de SQLite ni un cambio que la aplicación realice automáticamente. El servidor
local y los permisos del archivo reducen exposición, pero no sustituyen el
control de acceso del sistema operativo.

## 7. Detener y resolver problemas

- Detén Flask con **Ctrl+C** en la primera ventana.
- Si `ModuleNotFoundError: flask` aparece, repite la instalación de Flask en el
  entorno `.venv` con el comando de la sección 1.
- Si las pruebas dicen que no se pudo conectar, confirma que Flask sigue
  ejecutándose en el puerto 5000.
- Si el puerto 5000 ya está ocupado, identifica y detén el servicio local que
  lo usa o inicia este laboratorio con `--port 5001`; pasa también
  `--port 5001` al script de pruebas y escanea ese puerto.

`app_vulnerable.py` contiene código intencionalmente vulnerable. Úsalo solo en
esta práctica local, con datos ficticios; no lo despliegues en Internet.
