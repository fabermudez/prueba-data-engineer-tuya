-- Calcula, para cada cliente, la racha de meses consecutivos en un mismo
-- nivel de saldo que cumpla con una longitud mínima :n, "parado" en una
-- fecha :fecha_base.
--
-- Parámetros (named parameters de sqlite3): :fecha_base (YYYY-MM-DD), :n (entero)

WITH RECURSIVE
parametros AS (
    SELECT date(:fecha_base) AS fecha_base, :n AS n_min
),

-- 1) Rango de análisis por cliente: desde su primera aparición hasta
--    min(fecha_base, fecha_retiro). Si el cliente se retiró antes de
--    fecha_base, no se generan meses posteriores al retiro (no se
--    rellenan con N0 después de que el cliente se fue).
cliente_rango AS (
    SELECT
        h.identificacion,
        MIN(h.corte_mes) AS fecha_inicio,
        CASE
            WHEN r.fecha_retiro IS NOT NULL
                 AND r.fecha_retiro <= (SELECT fecha_base FROM parametros)
                THEN r.fecha_retiro
            ELSE (SELECT fecha_base FROM parametros)
        END AS fecha_fin
    FROM historia h
    LEFT JOIN retiros r ON r.identificacion = h.identificacion
    WHERE h.corte_mes <= (SELECT fecha_base FROM parametros)
    GROUP BY h.identificacion
    HAVING MIN(h.corte_mes) <= fecha_fin
),

-- 2) Generamos la grilla completa de fin-de-mes entre fecha_inicio y
--    fecha_fin para cada cliente (aunque no tenga registro en 'historia'
--    para ese mes).
meses AS (
    SELECT identificacion, fecha_inicio AS corte_mes, fecha_fin
    FROM cliente_rango

    UNION ALL

    SELECT
        identificacion,
        date(corte_mes, 'start of month', '+2 months', '-1 day') AS corte_mes,
        fecha_fin
    FROM meses
    WHERE date(corte_mes, 'start of month', '+2 months', '-1 day') <= fecha_fin
),

-- 3) Saldo real si existe, 0 si el mes no aparece en 'historia'
historia_completa AS (
    SELECT
        m.identificacion,
        m.corte_mes,
        COALESCE(h.saldo, 0) AS saldo
    FROM meses m
    LEFT JOIN historia h
        ON h.identificacion = m.identificacion AND h.corte_mes = m.corte_mes
),

-- 4) Clasificación por nivel según el enunciado
niveles AS (
    SELECT
        identificacion,
        corte_mes,
        saldo,
        CASE
            WHEN saldo >= 5000000 THEN 'N4'
            WHEN saldo >= 3000000 THEN 'N3'
            WHEN saldo >= 1000000 THEN 'N2'
            WHEN saldo >=  300000 THEN 'N1'
            ELSE 'N0'
        END AS nivel
    FROM historia_completa
),

-- 5) Técnica "islands and gaps": la diferencia entre el número de fila
--    general y el número de fila particionado por (cliente, nivel) es
--    constante mientras el nivel no cambie mes a mes -> identifica la racha.
con_grupo AS (
    SELECT
        identificacion,
        corte_mes,
        nivel,
        ROW_NUMBER() OVER (PARTITION BY identificacion ORDER BY corte_mes)
            - ROW_NUMBER() OVER (PARTITION BY identificacion, nivel ORDER BY corte_mes)
            AS grupo_racha
    FROM niveles
),

-- 6) Longitud y fecha_fin de cada racha
rachas AS (
    SELECT
        identificacion,
        nivel,
        grupo_racha,
        COUNT(*)      AS racha,
        MAX(corte_mes) AS fecha_fin
    FROM con_grupo
    GROUP BY identificacion, nivel, grupo_racha
),

-- 7) Filtro por longitud mínima n
rachas_filtradas AS (
    SELECT *
    FROM rachas
    WHERE racha >= (SELECT n_min FROM parametros)
),

-- 8) Desempate: racha más larga primero, luego fecha_fin más reciente
rachas_rankeadas AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY identificacion
            ORDER BY racha DESC, fecha_fin DESC
        ) AS orden
    FROM rachas_filtradas
)

SELECT identificacion, racha, fecha_fin, nivel
FROM rachas_rankeadas
WHERE orden = 1
ORDER BY identificacion;
