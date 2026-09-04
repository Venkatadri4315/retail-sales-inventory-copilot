import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "retail.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("PS03 DATASET BUSINESS SCENARIO CHECK")
print("=" * 70)


# ------------------------------------------------------------
# 1. Basic counts
# ------------------------------------------------------------

print("\n1. BASIC COUNTS")
print("-" * 70)

for table in [
    "stores",
    "products",
    "sales",
    "inventory",
    "business_events",
]:
    count = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table:20} {count:,}")


# ------------------------------------------------------------
# 2. Stock-out candidates
# ------------------------------------------------------------

print("\n2. STOCK-OUT RISK CANDIDATES")
print("-" * 70)

query = """
SELECT
    i.store_id,
    i.product_id,
    p.product_name,
    i.closing_stock,
    p.reorder_level,
    ROUND(
        SUM(s.units_sold) / 7.0,
        2
    ) AS avg_daily_sales,
    ROUND(
        i.closing_stock /
        NULLIF(SUM(s.units_sold) / 7.0, 0),
        2
    ) AS days_remaining
FROM inventory i
JOIN products p
    ON i.product_id = p.product_id
JOIN sales s
    ON i.store_id = s.store_id
    AND i.product_id = s.product_id
    AND s.sale_date >= '2026-08-23'
WHERE i.inventory_date = '2026-08-29'
GROUP BY
    i.store_id,
    i.product_id
HAVING
    i.closing_stock <= p.reorder_level
    AND avg_daily_sales > 0
ORDER BY days_remaining ASC
LIMIT 10
"""

rows = cursor.execute(query).fetchall()

for row in rows:
    print(
        f"Store={row[0]} | "
        f"Product={row[1]} ({row[2]}) | "
        f"Stock={row[3]} | "
        f"Reorder={row[4]} | "
        f"Avg/day={row[5]} | "
        f"Days={row[6]}"
    )

print(f"Found: {len(rows)}")


# ------------------------------------------------------------
# 3. Overstock candidates
# ------------------------------------------------------------

print("\n3. OVERSTOCK CANDIDATES")
print("-" * 70)

query = """
SELECT
    i.store_id,
    i.product_id,
    p.product_name,
    i.closing_stock,
    p.target_stock,
    ROUND(
        SUM(s.units_sold) / 7.0,
        2
    ) AS avg_daily_sales
FROM inventory i
JOIN products p
    ON i.product_id = p.product_id
JOIN sales s
    ON i.store_id = s.store_id
    AND i.product_id = s.product_id
    AND s.sale_date >= '2026-08-23'
WHERE i.inventory_date = '2026-08-29'
GROUP BY
    i.store_id,
    i.product_id
HAVING
    i.closing_stock > p.target_stock * 1.5
    AND avg_daily_sales < p.reorder_level * 0.3
ORDER BY i.closing_stock DESC
LIMIT 10
"""

rows = cursor.execute(query).fetchall()

for row in rows:
    print(
        f"Store={row[0]} | "
        f"Product={row[1]} ({row[2]}) | "
        f"Stock={row[3]} | "
        f"Target={row[4]} | "
        f"Avg/day={row[5]}"
    )

print(f"Found: {len(rows)}")


# ------------------------------------------------------------
# 4. Non-moving products
# ------------------------------------------------------------

print("\n4. NON-MOVING PRODUCTS")
print("-" * 70)

query = """
SELECT
    i.store_id,
    i.product_id,
    p.product_name,
    i.closing_stock,
    COALESCE(SUM(s.units_sold), 0) AS units_sold_30d
FROM inventory i
JOIN products p
    ON i.product_id = p.product_id
LEFT JOIN sales s
    ON i.store_id = s.store_id
    AND i.product_id = s.product_id
    AND s.sale_date >= '2026-07-31'
WHERE i.inventory_date = '2026-08-29'
GROUP BY
    i.store_id,
    i.product_id
HAVING
    i.closing_stock > 10
    AND units_sold_30d <= 2
ORDER BY i.closing_stock DESC
LIMIT 10
"""

rows = cursor.execute(query).fetchall()

for row in rows:
    print(
        f"Store={row[0]} | "
        f"Product={row[1]} ({row[2]}) | "
        f"Stock={row[3]} | "
        f"30-day sales={row[4]}"
    )

print(f"Found: {len(rows)}")


# ------------------------------------------------------------
# 5. Sales spikes
# ------------------------------------------------------------

print("\n5. SALES SPIKE CANDIDATES")
print("-" * 70)

query = """
WITH recent AS (
    SELECT
        store_id,
        product_id,
        SUM(units_sold) / 7.0 AS avg_7d
    FROM sales
    WHERE sale_date >= '2026-08-23'
    GROUP BY store_id, product_id
),
baseline AS (
    SELECT
        store_id,
        product_id,
        SUM(units_sold) / 23.0 AS avg_prior_23d
    FROM sales
    WHERE sale_date >= '2026-07-31'
      AND sale_date < '2026-08-23'
    GROUP BY store_id, product_id
)
SELECT
    r.store_id,
    r.product_id,
    p.product_name,
    ROUND(r.avg_7d, 2),
    ROUND(b.avg_prior_23d, 2),
    ROUND(r.avg_7d / b.avg_prior_23d, 2)
FROM recent r
JOIN baseline b
    ON r.store_id = b.store_id
    AND r.product_id = b.product_id
JOIN products p
    ON r.product_id = p.product_id
WHERE b.avg_prior_23d > 0
  AND r.avg_7d >= b.avg_prior_23d * 2
ORDER BY r.avg_7d / b.avg_prior_23d DESC
LIMIT 10
"""

rows = cursor.execute(query).fetchall()

for row in rows:
    print(
        f"Store={row[0]} | "
        f"Product={row[1]} ({row[2]}) | "
        f"Recent={row[3]}/day | "
        f"Previous={row[4]}/day | "
        f"Ratio={row[5]}x"
    )

print(f"Found: {len(rows)}")


# ------------------------------------------------------------
# 6. Sales drops
# ------------------------------------------------------------

print("\n6. SALES DROP CANDIDATES")
print("-" * 70)

query = """
WITH recent AS (
    SELECT
        store_id,
        product_id,
        SUM(units_sold) / 7.0 AS avg_7d
    FROM sales
    WHERE sale_date >= '2026-08-23'
    GROUP BY store_id, product_id
),
baseline AS (
    SELECT
        store_id,
        product_id,
        SUM(units_sold) / 23.0 AS avg_prior_23d
    FROM sales
    WHERE sale_date >= '2026-07-31'
      AND sale_date < '2026-08-23'
    GROUP BY store_id, product_id
)
SELECT
    r.store_id,
    r.product_id,
    p.product_name,
    ROUND(r.avg_7d, 2),
    ROUND(b.avg_prior_23d, 2),
    ROUND(r.avg_7d / b.avg_prior_23d, 2)
FROM recent r
JOIN baseline b
    ON r.store_id = b.store_id
    AND r.product_id = b.product_id
JOIN products p
    ON r.product_id = p.product_id
WHERE b.avg_prior_23d > 0
  AND r.avg_7d <= b.avg_prior_23d * 0.5
ORDER BY r.avg_7d / b.avg_prior_23d ASC
LIMIT 10
"""

rows = cursor.execute(query).fetchall()

for row in rows:
    print(
        f"Store={row[0]} | "
        f"Product={row[1]} ({row[2]}) | "
        f"Recent={row[3]}/day | "
        f"Previous={row[4]}/day | "
        f"Ratio={row[5]}x"
    )

print(f"Found: {len(rows)}")


# ------------------------------------------------------------
# 7. Business events
# ------------------------------------------------------------

print("\n7. BUSINESS EVENTS")
print("-" * 70)

rows = cursor.execute(
    """
    SELECT event_type, COUNT(*)
    FROM business_events
    GROUP BY event_type
    ORDER BY event_type
    """
).fetchall()

for event_type, count in rows:
    print(f"{event_type:20} {count}")


# ------------------------------------------------------------
# 8. Database integrity
# ------------------------------------------------------------

print("\n8. SQLITE INTEGRITY")
print("-" * 70)

result = cursor.execute(
    "PRAGMA integrity_check"
).fetchone()[0]

print(result)


conn.close()

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)