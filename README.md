# Prueba Técnica — Ingeniería de Datos (Tuya)

Solución a los 4 ejercicios de la prueba técnica para el cargo de Ingeniero de
Datos. Cada ejercicio está en su propia carpeta, con su propio README explicando
el desarrollo, las decisiones de diseño y cómo replicarlo.

## Estructura del repositorio

```
.
├── ejercicio1/
│   └── README.md          # Diseño CI/CD del dataset de teléfonos (conceptual)
├── ejercicio2/
│   └── README.md          # KPIs y veeduría de calidad de datos (conceptual)
├── ejercicio3/
│   ├── data/
│   │   └── Rachas.xlsx
│   ├── 01_crear_y_cargar_db.py
│   ├── rachas.sql
│   ├── 02_ejecutar_rachas.py
│   └── README.md          # Rachas de nivel de saldo en SQL (SQLite)
├── ejercicio4/
│   ├── html_image_embedder.py
│   └── README.md          # Procesamiento de imágenes HTML a base64 (Python)
├── .gitignore
└── README.md              # Este archivo
```

## Resumen de cada ejercicio

### Ejercicio 1 — Diseño CI/CD del dataset de teléfonos
Propuesta conceptual de un flujo de ingesta, estandarización y validación de
números de teléfono (arquitectura medallion bronze/silver/gold), con un pipeline
de CI/CD que corre pruebas automatizadas antes de desplegar cualquier cambio a
producción. Incluye diagramas del flujo de datos y del pipeline de CI/CD.
📄 [Ver detalle](./ejercicio1/README.md)

### Ejercicio 2 — KPIs y veeduría de calidad de datos
A partir del proceso del ejercicio 1, define KPIs de calidad (completitud,
duplicados, % en cuarentena, freshness) y de trazabilidad (linaje del dato),
junto con el mecanismo para calcularlos y exponerlos a distintos consumidores
del negocio.
📄 [Ver detalle](./ejercicio2/README.md)

### Ejercicio 3 — Rachas de nivel de saldo (SQL)
Carga de `Rachas.xlsx` a SQLite y una consulta parametrizada (`fecha_base`, `n`)
que identifica, por cliente, la racha de meses consecutivos en un mismo nivel de
saldo, con desempate por longitud y luego por fecha más reciente. Probado
contra los datos reales provistos.
📄 [Ver detalle](./ejercicio3/README.md)

### Ejercicio 4 — Procesamiento de imágenes HTML a base64
Script en Python (solo librería estándar, orientado a objetos) que recorre
archivos o directorios HTML (incluyendo subdirectorios), embebe cada imagen
referenciada en `<img>` como base64, y genera un archivo nuevo sin modificar el
original, reportando éxitos y fallos por archivo.
📄 [Ver detalle](./ejercicio4/README.md)

## Cómo correr cada ejercicio

Los ejercicios 1 y 2 son conceptuales (no requieren ejecución). Para los
ejercicios 3 y 4:

```bash
pip install pandas openpyxl

# Ejercicio 3
cd ejercicio3
python 01_crear_y_cargar_db.py data/Rachas.xlsx rachas.db
python 02_ejecutar_rachas.py 2024-12-31 3 rachas.db resultado.csv

# Ejercicio 4
cd ../ejercicio4
python html_image_embedder.py carpeta_con_htmls/
```

## Autor

Felipe — Ingeniero de Sistemas y Telecomunicaciones, con experiencia en
Microsoft Fabric, Salesforce (Data Cloud / Data 360), SQL y Python.
