"""
Crea la base de datos SQLite y carga los datos de rachas.xlsx.

Uso:
    python 01_crear_y_cargar_db.py [ruta_excel] [ruta_db]

Por defecto usa Rachas.xlsx y rachas.db en el directorio actual.
"""
import sqlite3
import sys

import pandas as pd


def crear_esquema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS historia;
        DROP TABLE IF EXISTS retiros;

        CREATE TABLE historia (
            identificacion TEXT NOT NULL,
            corte_mes      DATE NOT NULL,
            saldo          REAL NOT NULL,
            PRIMARY KEY (identificacion, corte_mes)
        );

        CREATE TABLE retiros (
            identificacion TEXT PRIMARY KEY,
            fecha_retiro   DATE NOT NULL
        );

        CREATE INDEX idx_historia_cliente ON historia(identificacion);
        """
    )


def cargar_datos(conn: sqlite3.Connection, excel_path: str) -> None:
    historia = pd.read_excel(excel_path, sheet_name="historia")
    retiros = pd.read_excel(excel_path, sheet_name="retiros").dropna(how="all")

    # Normalizamos las fechas a texto ISO (YYYY-MM-DD) para que las
    # comparaciones y funciones date() de SQLite funcionen correctamente.
    historia["corte_mes"] = pd.to_datetime(historia["corte_mes"]).dt.strftime("%Y-%m-%d")
    retiros["fecha_retiro"] = pd.to_datetime(retiros["fecha_retiro"]).dt.strftime("%Y-%m-%d")

    # Control de calidad básico antes de cargar
    duplicados = historia.duplicated(subset=["identificacion", "corte_mes"]).sum()
    if duplicados:
        print(f"[AVISO] {duplicados} registros duplicados (identificacion, corte_mes) "
              f"en 'historia' — se conserva el último.")
        historia = historia.drop_duplicates(subset=["identificacion", "corte_mes"], keep="last")

    nulos_saldo = historia["saldo"].isna().sum()
    if nulos_saldo:
        print(f"[AVISO] {nulos_saldo} registros con saldo nulo en 'historia' — se descartan.")
        historia = historia.dropna(subset=["saldo"])

    historia.to_sql("historia", conn, if_exists="append", index=False)
    retiros.to_sql("retiros", conn, if_exists="append", index=False)


def main() -> None:
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "Rachas.xlsx"
    db_path = sys.argv[2] if len(sys.argv) > 2 else "rachas.db"

    conn = sqlite3.connect(db_path)
    try:
        crear_esquema(conn)
        cargar_datos(conn, excel_path)
        conn.commit()

        n_historia = conn.execute("SELECT COUNT(*) FROM historia").fetchone()[0]
        n_retiros = conn.execute("SELECT COUNT(*) FROM retiros").fetchone()[0]
        print(f"Base de datos creada en: {db_path}")
        print(f"  historia: {n_historia} registros")
        print(f"  retiros:  {n_retiros} registros")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
