# Ejercicio 4: Procesamiento de imágenes en HTML (a base64)

## Objetivo

Diseñar script(s) en Python que:

1. Reciban un listado de archivos HTML y/o de directorios que contengan
   archivos HTML (recorriendo subdirectorios).
2. Por cada archivo, detecten las imágenes asociadas (referenciadas con el tag
   `<img>`) y las conviertan a base64.
3. Reemplacen las imágenes originales por las codificadas en base64 dentro del
   HTML, **sin sustituir el archivo original** (creando uno nuevo).
4. Generen un objeto `{ success: {}, fail: {} }` con las imágenes procesadas
   exitosamente y las que fallaron.

## Herramienta / restricciones

Solo **librería estándar** de Python: `re`, `base64`, `mimetypes`, `pathlib`,
`argparse`, `json`, `dataclasses`. No se usó ningún parser HTML de terceros
(como BeautifulSoup) ni librerías de imágenes.

## Estructura de archivos

```
ejercicio4/
├── html_image_embedder.py
└── README.md
```

## Diseño (orientado a objetos, principios SOLID)

| Clase | Responsabilidad única |
|---|---|
| `ImageToBase64Converter` | Leer una imagen del disco y devolver su Data URI en base64, infiriendo el tipo MIME con `mimetypes`. |
| `HtmlImageEmbedder` | Procesar el contenido de **un** HTML: localizar cada `<img src="...">` con una expresión regular y reemplazar el `src` por el Data URI, delegando la codificación al `ImageToBase64Converter`. |
| `HtmlFileFinder` | Resolver una lista de rutas (archivos y/o directorios) a la lista final de archivos `.html`/`.htm` a procesar, recorriendo subdirectorios con `rglob`. |
| `BatchProcessor` | Orquestar todo el flujo: encontrar archivos, procesarlos, escribir el archivo nuevo y construir el reporte `{success, fail}`. |

Cada clase depende de una abstracción simple (por ejemplo, `HtmlImageEmbedder`
recibe un `converter` en su constructor), lo que permite sustituir la forma de
codificar imágenes sin tocar el resto del código (inversión de dependencias).

### Por qué expresiones regulares y no un parser HTML completo

El ejercicio solo requiere localizar y reemplazar el atributo `src` dentro de
tags `<img>`, preservando el resto del documento exactamente igual (incluyendo
espacios, otros atributos y el resto del HTML). Un parser DOM completo
reconstruye el árbol y puede alterar formato o escritura de otros tags; una
expresión regular acotada al patrón `<img ... src="...">` cumple el requisito
con menor riesgo de modificar algo que no se pidió cambiar.

## Manejo de casos y decisiones de diseño

- **Imagen no encontrada en disco** → se reporta en `fail` con el motivo, y el
  `<img>` se deja intacto en el HTML de salida.
- **Imagen ya en base64** (`src="data:..."`) → se omite (no se reprocesa, no
  cuenta como éxito ni como fallo).
- **URLs externas** (`http://`, `https://`) → se reportan en `fail` con el
  motivo `"URL externa no soportada"`. Se decidió no descargar imágenes
  remotas para mantener el script determinístico y sin dependencia de red
  durante la evaluación; queda como una extensión natural usando `urllib`
  (también estándar) si se requiere.
- **Archivo de salida**: se genera junto al original con el sufijo `_base64`
  (p. ej. `pagina.html` → `pagina_base64.html`), nunca sobrescribe el archivo
  original.

## Formato del reporte

El reporte se agrupa por archivo procesado, para poder ubicar exactamente en
qué HTML falló cada imagen:

```json
{
  "success": {
    "prueba/pagina1.html": ["img/logo.png"],
    "prueba/sub/pagina2.html": ["foto.png"]
  },
  "fail": {
    "prueba/pagina1.html": {
      "img/no_existe.png": "No se encontró la imagen: ..."
    },
    "prueba/sub/pagina2.html": {
      "https://ejemplo.com/remota.png": "URL externa no soportada (solo imágenes locales)"
    }
  }
}
```

## Cómo correrlo

```bash
# Un archivo
python html_image_embedder.py pagina.html

# Varios archivos y/o directorios (se recorren subdirectorios)
python html_image_embedder.py pagina1.html carpeta_con_htmls/

# Como librería
python -c "
from html_image_embedder import BatchProcessor
print(BatchProcessor().run(['carpeta_con_htmls']))
"
```

## Pruebas realizadas

Se probó con un set de archivos que incluye: una imagen local existente, una
imagen local inexistente, una imagen dentro de una subcarpeta, y una imagen
referenciada por URL externa — confirmando que el reporte `success`/`fail`
clasifica correctamente cada caso y que los archivos originales no se
modifican.
