"""
Ejercicio 4: convierte a base64 las imágenes referenciadas con <img> dentro de
archivos HTML, generando un nuevo archivo (nunca sobrescribe el original).

Solo usa librerías estándar de Python (re, base64, mimetypes, pathlib, argparse, json).

Uso como script:
    python html_image_embedder.py archivo1.html archivo2.html
    python html_image_embedder.py carpeta_con_htmls/
    python html_image_embedder.py archivo1.html carpeta/  # listas mixtas también funcionan

Uso como librería:
    from html_image_embedder import BatchProcessor
    resultado = BatchProcessor().run(["carpeta_con_htmls"])
    # resultado = {"success": {...}, "fail": {...}}
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# --------------------------------------------------------------------------- #
# 1) Conversión de una imagen individual a base64 (Data URI)
# --------------------------------------------------------------------------- #
class ImageToBase64Converter:
    """Convierte el contenido binario de una imagen a un Data URI base64."""

    @staticmethod
    def encode(image_path: Path) -> str:
        if not image_path.is_file():
            raise FileNotFoundError(f"No se encontró la imagen: {image_path}")

        mime_type, _ = mimetypes.guess_type(image_path.name)
        mime_type = mime_type or "application/octet-stream"

        contenido = image_path.read_bytes()
        codificado = base64.b64encode(contenido).decode("ascii")
        return f"data:{mime_type};base64,{codificado}"


# --------------------------------------------------------------------------- #
# 2) Resultado de procesar un único archivo HTML
# --------------------------------------------------------------------------- #
@dataclass
class ArchivoResultado:
    success: list[str] = field(default_factory=list)
    fail: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# 3) Procesador de un archivo HTML: detecta <img>, reemplaza src por base64
# --------------------------------------------------------------------------- #
class HtmlImageEmbedder:
    """
    Busca tags <img ... src="..." ...> con una expresión regular (no se usa un
    parser DOM completo porque solo se necesita localizar y reemplazar el
    atributo src, preservando el resto del documento intacto).
    """

    _IMG_SRC_PATTERN = re.compile(
        r"""<img\b[^>]*?\bsrc\s*=\s*(?P<quote>['"])(?P<src>.*?)(?P=quote)[^>]*>""",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(self, converter: ImageToBase64Converter | None = None) -> None:
        self.converter = converter or ImageToBase64Converter()

    def process(self, html_path: Path) -> tuple[str, ArchivoResultado]:
        """Devuelve (html_transformado, resultado) sin escribir nada a disco."""
        html_original = html_path.read_text(encoding="utf-8")
        resultado = ArchivoResultado()
        base_dir = html_path.parent

        def reemplazar(match: re.Match) -> str:
            src = match.group("src")

            if src.startswith("data:"):
                # Ya está embebida en base64, no hay nada que hacer.
                return match.group(0)

            if src.startswith(("http://", "https://")):
                # Fuera de alcance sin acceso a red garantizado; se reporta como fallo.
                resultado.fail[src] = "URL externa no soportada (solo imágenes locales)"
                return match.group(0)

            imagen_path = (base_dir / src).resolve()
            try:
                data_uri = self.converter.encode(imagen_path)
            except Exception as exc:  # noqa: BLE001 - se reporta cualquier fallo de lectura
                resultado.fail[src] = str(exc)
                return match.group(0)

            resultado.success.append(src)

            tag_completo = match.group(0)
            inicio_src = match.start("src") - match.start(0)
            fin_src = match.end("src") - match.start(0)
            return tag_completo[:inicio_src] + data_uri + tag_completo[fin_src:]

        html_transformado = self._IMG_SRC_PATTERN.sub(reemplazar, html_original)
        return html_transformado, resultado


# --------------------------------------------------------------------------- #
# 4) Localización de archivos HTML a partir de rutas de archivo y/o directorio
# --------------------------------------------------------------------------- #
class HtmlFileFinder:
    _EXTENSIONES = (".html", ".htm")

    def encontrar(self, rutas: Iterable[str]) -> list[Path]:
        encontrados: list[Path] = []
        for ruta_str in rutas:
            ruta = Path(ruta_str)
            if ruta.is_file() and ruta.suffix.lower() in self._EXTENSIONES:
                encontrados.append(ruta)
            elif ruta.is_dir():
                for extension in self._EXTENSIONES:
                    encontrados.extend(sorted(ruta.rglob(f"*{extension}")))
            else:
                print(f"[AVISO] Ruta ignorada (no existe o no es HTML): {ruta}")
        return encontrados


# --------------------------------------------------------------------------- #
# 5) Orquestador: procesa un lote de archivos/directorios y arma el reporte
# --------------------------------------------------------------------------- #
class BatchProcessor:
    SUFIJO_SALIDA = "_base64"

    def __init__(self) -> None:
        self.finder = HtmlFileFinder()
        self.embedder = HtmlImageEmbedder()

    def run(self, rutas: Iterable[str]) -> dict:
        archivos_html = self.finder.encontrar(rutas)
        reporte: dict[str, dict] = {"success": {}, "fail": {}}

        for archivo in archivos_html:
            html_transformado, resultado = self.embedder.process(archivo)
            self._escribir_nuevo_archivo(archivo, html_transformado)

            if resultado.success:
                reporte["success"][str(archivo)] = resultado.success
            if resultado.fail:
                reporte["fail"][str(archivo)] = resultado.fail

        return reporte

    def _escribir_nuevo_archivo(self, archivo_original: Path, contenido: str) -> Path:
        nuevo_nombre = f"{archivo_original.stem}{self.SUFIJO_SALIDA}{archivo_original.suffix}"
        nuevo_path = archivo_original.with_name(nuevo_nombre)
        nuevo_path.write_text(contenido, encoding="utf-8")
        return nuevo_path


# --------------------------------------------------------------------------- #
# 6) CLI
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convierte a base64 las imágenes de archivos HTML (o carpetas de HTML)."
    )
    parser.add_argument(
        "rutas",
        nargs="+",
        help="Uno o más archivos .html y/o directorios (se recorren recursivamente).",
    )
    args = parser.parse_args()

    reporte = BatchProcessor().run(args.rutas)
    print(json.dumps(reporte, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
