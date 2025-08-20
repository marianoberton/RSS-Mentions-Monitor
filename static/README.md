# Static Files

Este directorio contiene archivos estáticos para la interfaz web.

## Estructura

- `css/` - Archivos de estilos CSS
- `js/` - Archivos JavaScript
- `images/` - Imágenes y recursos gráficos
- `fonts/` - Fuentes personalizadas

## Uso

Los archivos en este directorio son servidos directamente por Flask en la ruta `/static/`.

Ejemplo:
- `static/css/style.css` → `http://localhost:5000/static/css/style.css`
- `static/js/app.js` → `http://localhost:5000/static/js/app.js`