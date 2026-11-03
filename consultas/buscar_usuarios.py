"""Consultas de búsqueda sobre la tabla usuarios."""

# Consulta intencionalmente vulnerable para el laboratorio local.
# La aplicación inserta la entrada en el marcador {nombre} antes de ejecutarla.
buscar_usuarios_concatenada = (
    "SELECT id, nombre, correo AS dato FROM usuarios "
    "WHERE nombre LIKE '%{nombre}%'"
)

# Consulta segura: el valor de búsqueda se envía por separado como parámetro.
buscar_usuarios_parametrizada = (
    "SELECT id, nombre, correo AS dato FROM usuarios WHERE nombre LIKE ?"
)
