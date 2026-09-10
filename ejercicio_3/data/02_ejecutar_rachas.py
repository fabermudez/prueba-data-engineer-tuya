"""
Ejecuta rachas.sql contra la base de datos, parametrizado por fecha_base y n.

Uso:
    python 02_ejecutar_rachas.py <fecha_base:YYYY-MM-DD> <n> [ruta_db] [salida.csv]

Ejemplo:
    python 02_ejecutar_rachas.py 2024-12-31 3 rachas.db resultado.csv
"""
import csv
import sqlite3
import sys
from pathlib import Path


def ejecutar_rachas(db_path: str, fecha_base: str, n: int):
    query = Path(__file__).with_name("rachas.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(query, {"fecha_base": fecha_base, "n": n})
        columnas = [d[0] for d in cur.description]
        filas = cur.fetchall()
        return columnas, filas
    finally:
        conn.close()


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    fecha_base = sys.argv[1]
    n = int(sys.argv[2])
    db_path = sys.argv[3] if len(sys.argv) > 3 else "rachas.db"
    salida = sys.argv[4] if len(sys.argv) > 4 else None

    columnas, filas = ejecutar_rachas(db_path, fecha_base, n)

    print(f"fecha_base={fecha_base}  n={n}  -> {len(filas)} clientes con racha")
    for fila in filas[:15]:
        print(dict(zip(columnas, fila)))
    if len(filas) > 15:
        print(f"... ({len(filas) - 15} filas más)")

    if salida:
        with open(salida, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columnas)
            writer.writerows(filas)
        print(f"\nResultado exportado a {salida}")


if __name__ == "__main__":
    main()
