# Ejercicio 3: Rachas de nivel de saldo por cliente

## Objetivo

A partir de `Rachas.xlsx` (saldos de clientes por corte de mes), cargar los datos a
una base de datos y generar una consulta que, "parada" en una `fecha_base`,
identifique para cada cliente la racha de meses consecutivos en un mismo nivel de
saldo que cumpla con una longitud mínima `n`.

## Herramienta utilizada

**SQLite**, por tres razones:

- No requiere servidor ni instalación adicional — cualquiera puede correr los
  scripts y obtener el mismo resultado.
- Soporta CTEs recursivos y funciones de ventana (`ROW_NUMBER() OVER`), que son
  la base de la solución.
- Al ser un único archivo `.db`, hace la entrega totalmente reproducible.

## Estructura de archivos

```
ejercicio3/
├── data/
│   └── Rachas.xlsx              # archivo original provisto
├── 01_crear_y_cargar_db.py      # crea el esquema y carga los datos
├── rachas.sql                   # consulta parametrizada (fecha_base, n)
├── 02_ejecutar_rachas.py        # ejecuta rachas.sql con parámetros y exporta a CSV
└── README.md
```

## Cómo replicar la solución

```bash
pip install pandas openpyxl

python 01_crear_y_cargar_db.py data/Rachas.xlsx rachas.db
python 02_ejecutar_rachas.py 2024-12-31 3 rachas.db resultado.csv
```

El segundo script recibe `fecha_base` y `n` como parámetros de línea de comandos,
tal como pide el enunciado ("permita realizar todo el ejercicio con base en una
fecha específica"). Ejemplo real corrido contra los datos provistos
(`fecha_base=2024-12-31`, `n=3`): **91 clientes** con al menos una racha que cumple
el criterio.

## Modelo de datos

| Tabla | Columnas | Notas |
|---|---|---|
| `historia` | `identificacion`, `corte_mes`, `saldo` | Llave primaria `(identificacion, corte_mes)` |
| `retiros` | `identificacion`, `fecha_retiro` | Llave primaria `identificacion` |

Durante la carga (`01_crear_y_cargar_db.py`) se aplican controles de calidad
básicos: se eliminan duplicados de `(identificacion, corte_mes)` conservando el
último valor, y se descartan registros con `saldo` nulo, reportando en consola
cuántos se afectaron.

## Lógica de la consulta (`rachas.sql`)

1. **Rango de análisis por cliente**: desde su primera aparición en `historia`
   hasta `min(fecha_base, fecha_retiro)`.
2. **Grilla completa de meses**: un CTE recursivo genera todos los fin-de-mes
   entre el inicio y el fin del rango, incluso los meses sin registro.
3. **Relleno con N0**: los meses generados sin coincidencia en `historia` reciben
   `saldo = 0`, que cae en el nivel N0.
4. **Clasificación por nivel**: `CASE WHEN` con los rangos N0–N4 del enunciado.
5. **Detección de rachas ("islands and gaps")**: la diferencia entre el número de
   fila general del cliente y el número de fila particionado por
   `(cliente, nivel)` es constante mientras el nivel no cambie — eso agrupa los
   meses consecutivos de una misma racha.
6. **Filtro por `n`**: se descartan las rachas con longitud menor a `n`.
7. **Desempate**: si un cliente tiene varias rachas válidas, se elige primero la
   más larga y, en caso de empate, la de `fecha_fin` más reciente
   (`ROW_NUMBER()` sobre `racha DESC, fecha_fin DESC`).

## Decisión de diseño importante (a validar con el evaluador)

El enunciado dice: *"Si un cliente no aparece en un mes específico... se
considera que su saldo es N0, excepto si el corte de mes es superior a su fecha
de retiro"*. Se interpretó que, una vez superada la fecha de retiro, **se deja de
generar meses para ese cliente** (ni siquiera se asume N0) — es decir, la racha
no puede extenderse ni depender de meses posteriores al retiro. Si la intención
del enunciado era otra (p. ej. seguir asignando N0 indefinidamente después del
retiro), el único cambio necesario está en el CTE `cliente_rango` de `rachas.sql`.

## Supuestos adicionales

- `corte_mes` en `historia` siempre corresponde al último día del mes
  (confirmado en los datos provistos), por lo que la generación de la grilla de
  meses usa aritmética de fin de mes.
- Un cliente sin registros en `retiros` se asume activo indefinidamente (su
  rango de análisis llega hasta `fecha_base`).
- Se resolvió con SQL puro (CTEs + funciones de ventana) en lugar de lógica en
  Python, para que la solución quede autocontenida en la base de datos y sea
  fácilmente auditable como una sola consulta.
