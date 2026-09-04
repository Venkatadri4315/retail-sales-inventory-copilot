import sqlite3
from pathlib import Path


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "retail.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    """
    Create a SQLite connection with dictionary-style rows.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# 1. STOCK-OUT RISK
# =========================================================

def get_stockout_risks(limit=20):
    """
    Identify and rank the highest-priority stock-out risks.

    Evidence:
    - Latest closing stock
    - Reorder level
    - Units sold in last 14 days
    - Average daily sales
    - Estimated days of stock remaining
    - Stock vs reorder ratio

    Conditions:
    - Current stock <= reorder level
    - At least 5 units sold in last 14 days
    - Estimated stock <= 7 days

    Risk levels:
    - CRITICAL -> stock is zero
    - HIGH     -> 2 days or less
    - MEDIUM   -> 7 days or less

    Only the highest-priority candidates are returned.
    """

    conn = get_connection()

    query = """
    WITH latest_inventory AS (

        SELECT
            i.store_id,
            i.product_id,
            i.inventory_date,
            i.closing_stock,

            ROW_NUMBER() OVER (
                PARTITION BY i.store_id, i.product_id
                ORDER BY i.inventory_date DESC
            ) AS rn

        FROM inventory i
    ),

    recent_sales AS (

        SELECT
            s.store_id,
            s.product_id,

            SUM(s.units_sold) AS units_sold_14d

        FROM sales s

        WHERE s.sale_date >= (
            SELECT DATE(MAX(sale_date), '-13 days')
            FROM sales
        )

        GROUP BY
            s.store_id,
            s.product_id
    ),

    candidates AS (

        SELECT

            li.store_id,
            st.store_name,

            li.product_id,
            p.product_name,
            p.category,

            li.inventory_date,

            li.closing_stock,
            p.reorder_level,

            rs.units_sold_14d,

            ROUND(
                rs.units_sold_14d / 14.0,
                2
            ) AS avg_daily_sales,

            ROUND(
                li.closing_stock /
                NULLIF(
                    rs.units_sold_14d / 14.0,
                    0
                ),
                1
            ) AS days_of_stock,

            ROUND(
                CAST(li.closing_stock AS REAL)
                / NULLIF(p.reorder_level, 0),
                2
            ) AS stock_vs_reorder_ratio

        FROM latest_inventory li

        JOIN stores st
            ON st.store_id = li.store_id

        JOIN products p
            ON p.product_id = li.product_id

        JOIN recent_sales rs
            ON rs.store_id = li.store_id
            AND rs.product_id = li.product_id

        WHERE li.rn = 1

            AND li.closing_stock <= p.reorder_level

            AND rs.units_sold_14d >= 5

            AND (
                li.closing_stock /
                NULLIF(
                    rs.units_sold_14d / 14.0,
                    0
                )
            ) <= 7
    )

    SELECT
        *,

        CASE

            WHEN closing_stock = 0
                THEN 'CRITICAL'

            WHEN days_of_stock <= 2
                THEN 'HIGH'

            ELSE 'MEDIUM'

        END AS risk_level,

        CASE

            WHEN closing_stock = 0
                THEN 100

            WHEN days_of_stock <= 2
                THEN 80

            ELSE 50

        END

        +

        CASE

            WHEN stock_vs_reorder_ratio <= 0.5
                THEN 20

            WHEN stock_vs_reorder_ratio <= 1
                THEN 10

            ELSE 0

        END AS risk_score

    FROM candidates

    ORDER BY
        risk_score DESC,
        days_of_stock ASC,
        units_sold_14d DESC

    LIMIT ?;
    """

    rows = conn.execute(
        query,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# 2. OVERSTOCK
# =========================================================

def get_overstock_items(limit=20):
    """
    Identify products with excessive inventory.

    Conditions:
    - Current stock >= 2x target stock
    AND
    - No sales in last 30 days
      OR
    - At least 30 days of stock remaining.
    """

    conn = get_connection()

    query = """
    WITH latest_inventory AS (

        SELECT
            i.store_id,
            i.product_id,
            i.inventory_date,
            i.closing_stock,

            ROW_NUMBER() OVER (
                PARTITION BY i.store_id, i.product_id
                ORDER BY i.inventory_date DESC
            ) AS rn

        FROM inventory i
    ),

    recent_sales AS (

        SELECT
            s.store_id,
            s.product_id,

            SUM(s.units_sold) AS units_sold_30d

        FROM sales s

        WHERE s.sale_date >= (
            SELECT DATE(MAX(sale_date), '-29 days')
            FROM sales
        )

        GROUP BY
            s.store_id,
            s.product_id
    )

    SELECT

        li.store_id,
        st.store_name,

        li.product_id,
        p.product_name,
        p.category,

        li.inventory_date,

        li.closing_stock,
        p.target_stock,

        COALESCE(
            rs.units_sold_30d,
            0
        ) AS units_sold_30d,

        ROUND(
            COALESCE(rs.units_sold_30d, 0) / 30.0,
            2
        ) AS avg_daily_sales,

        CASE

            WHEN COALESCE(rs.units_sold_30d, 0) > 0

            THEN ROUND(
                li.closing_stock /
                (rs.units_sold_30d / 30.0),
                1
            )

            ELSE NULL

        END AS days_of_stock,

        ROUND(
            CAST(li.closing_stock AS REAL)
            / NULLIF(p.target_stock, 0),
            1
        ) AS stock_vs_target_ratio

    FROM latest_inventory li

    JOIN stores st
        ON st.store_id = li.store_id

    JOIN products p
        ON p.product_id = li.product_id

    LEFT JOIN recent_sales rs
        ON rs.store_id = li.store_id
        AND rs.product_id = li.product_id

    WHERE li.rn = 1

        AND li.closing_stock >=
            p.target_stock * 2

        AND (

            COALESCE(rs.units_sold_30d, 0) = 0

            OR

            (
                COALESCE(rs.units_sold_30d, 0) > 0

                AND

                li.closing_stock /
                (rs.units_sold_30d / 30.0) >= 30
            )
        )

    ORDER BY
        stock_vs_target_ratio DESC

    LIMIT ?;
    """

    rows = conn.execute(
        query,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# 3. NON-MOVING STOCK
# =========================================================

def get_non_moving_items(limit=20):
    """
    Identify products that have inventory but no sales
    during the last 30 days.
    """

    conn = get_connection()

    query = """
    WITH latest_inventory AS (

        SELECT
            i.store_id,
            i.product_id,
            i.inventory_date,
            i.closing_stock,

            ROW_NUMBER() OVER (
                PARTITION BY i.store_id, i.product_id
                ORDER BY i.inventory_date DESC
            ) AS rn

        FROM inventory i
    ),

    recent_sales AS (

        SELECT
            s.store_id,
            s.product_id,

            SUM(s.units_sold) AS units_sold_30d

        FROM sales s

        WHERE s.sale_date >= (
            SELECT DATE(MAX(sale_date), '-29 days')
            FROM sales
        )

        GROUP BY
            s.store_id,
            s.product_id
    )

    SELECT

        li.store_id,
        st.store_name,

        li.product_id,
        p.product_name,
        p.category,

        li.inventory_date,

        li.closing_stock,
        p.target_stock,

        COALESCE(
            rs.units_sold_30d,
            0
        ) AS units_sold_30d,

        ROUND(
            CAST(li.closing_stock AS REAL)
            / NULLIF(p.target_stock, 0),
            1
        ) AS stock_vs_target_ratio

    FROM latest_inventory li

    JOIN stores st
        ON st.store_id = li.store_id

    JOIN products p
        ON p.product_id = li.product_id

    LEFT JOIN recent_sales rs
        ON rs.store_id = li.store_id
        AND rs.product_id = li.product_id

    WHERE li.rn = 1

        AND li.closing_stock > 0

        AND COALESCE(
            rs.units_sold_30d,
            0
        ) = 0

    ORDER BY
        li.closing_stock DESC

    LIMIT ?;
    """

    rows = conn.execute(
        query,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# 4. PRODUCT SALES PERFORMANCE
# =========================================================

def get_product_performance(
    product_id=None,
    store_id=None
):
    """
    Calculate sales performance for a product/store.

    Optional filters:
        product_id
        store_id

    Returns:
        total units sold
        total revenue
        average daily units
    """

    conn = get_connection()

    query = """
    SELECT

        s.product_id,

        p.product_name,
        p.category,

        s.store_id,
        st.store_name,

        SUM(
            s.units_sold
        ) AS total_units_sold,

        ROUND(
            SUM(s.revenue),
            2
        ) AS total_revenue,

        ROUND(
            SUM(s.units_sold) / 90.0,
            2
        ) AS avg_daily_units

    FROM sales s

    JOIN products p
        ON p.product_id = s.product_id

    JOIN stores st
        ON st.store_id = s.store_id

    WHERE 1 = 1
    """

    params = []

    if product_id is not None:

        query += """
        AND s.product_id = ?
        """

        params.append(product_id)

    if store_id is not None:

        query += """
        AND s.store_id = ?
        """

        params.append(store_id)

    query += """
    GROUP BY

        s.product_id,
        p.product_name,
        p.category,

        s.store_id,
        st.store_name

    ORDER BY
        total_revenue DESC;
    """

    rows = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# 5. SALES SPIKES
# =========================================================

def get_sales_spikes(limit=20):
    """
    Identify products with unusually high recent sales.

    Comparison:
        Recent 7 days
        vs
        Previous 30 days

    Spike condition:
        Recent daily sales >= 1.8x baseline.
    """

    conn = get_connection()

    query = """
    WITH recent AS (

        SELECT
            store_id,
            product_id,

            SUM(units_sold) AS units_7d

        FROM sales

        WHERE sale_date >= (
            SELECT DATE(MAX(sale_date), '-6 days')
            FROM sales
        )

        GROUP BY
            store_id,
            product_id
    ),

    baseline AS (

        SELECT
            store_id,
            product_id,

            SUM(units_sold) AS units_previous_30d

        FROM sales

        WHERE sale_date >= (
            SELECT DATE(MAX(sale_date), '-36 days')
            FROM sales
        )

        AND sale_date < (
            SELECT DATE(MAX(sale_date), '-6 days')
            FROM sales
        )

        GROUP BY
            store_id,
            product_id
    )

    SELECT

        r.store_id,
        st.store_name,

        r.product_id,
        p.product_name,
        p.category,

        r.units_7d,

        ROUND(
            r.units_7d / 7.0,
            2
        ) AS recent_daily_sales,

        COALESCE(
            b.units_previous_30d,
            0
        ) AS units_previous_30d,

        ROUND(
            COALESCE(
                b.units_previous_30d,
                0
            ) / 30.0,
            2
        ) AS baseline_daily_sales,

        ROUND(
            (r.units_7d / 7.0) /
            NULLIF(
                b.units_previous_30d / 30.0,
                0
            ),
            2
        ) AS spike_ratio

    FROM recent r

    JOIN products p
        ON p.product_id = r.product_id

    JOIN stores st
        ON st.store_id = r.store_id

    LEFT JOIN baseline b
        ON b.store_id = r.store_id
        AND b.product_id = r.product_id

    WHERE

        COALESCE(
            b.units_previous_30d,
            0
        ) > 0

        AND

        (r.units_7d / 7.0) >=
        (b.units_previous_30d / 30.0) * 1.8

    ORDER BY
        spike_ratio DESC

    LIMIT ?;
    """

    rows = conn.execute(
        query,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# 6. SALES DROPS
# =========================================================

def get_sales_drops(limit=20):
    """
    Identify products with significant recent sales decline.

    Comparison:
        Recent 7 days
        vs
        Previous 30 days

    Drop condition:
        Recent daily sales <= 60% of baseline.
    """

    conn = get_connection()

    query = """
    WITH recent AS (

        SELECT
            store_id,
            product_id,

            SUM(units_sold) AS units_7d

        FROM sales

        WHERE sale_date >= (
            SELECT DATE(MAX(sale_date), '-6 days')
            FROM sales
        )

        GROUP BY
            store_id,
            product_id
    ),

    baseline AS (

        SELECT
            store_id,
            product_id,

            SUM(units_sold) AS units_previous_30d

        FROM sales

        WHERE sale_date >= (
            SELECT DATE(MAX(sale_date), '-36 days')
            FROM sales
        )

        AND sale_date < (
            SELECT DATE(MAX(sale_date), '-6 days')
            FROM sales
        )

        GROUP BY
            store_id,
            product_id
    )

    SELECT

        r.store_id,
        st.store_name,

        r.product_id,
        p.product_name,
        p.category,

        r.units_7d,

        ROUND(
            r.units_7d / 7.0,
            2
        ) AS recent_daily_sales,

        b.units_previous_30d,

        ROUND(
            b.units_previous_30d / 30.0,
            2
        ) AS baseline_daily_sales,

        ROUND(
            (r.units_7d / 7.0) /
            NULLIF(
                b.units_previous_30d / 30.0,
                0
            ),
            2
        ) AS recent_vs_baseline_ratio,

        ROUND(
            (
                1 -
                (
                    (r.units_7d / 7.0) /
                    NULLIF(
                        b.units_previous_30d / 30.0,
                        0
                    )
                )
            ) * 100,
            1
        ) AS decline_percentage

    FROM recent r

    JOIN baseline b
        ON b.store_id = r.store_id
        AND b.product_id = r.product_id

    JOIN products p
        ON p.product_id = r.product_id

    JOIN stores st
        ON st.store_id = r.store_id

    WHERE

        b.units_previous_30d > 0

        AND

        (r.units_7d / 7.0) <=
        (b.units_previous_30d / 30.0) * 0.60

    ORDER BY
        decline_percentage DESC

    LIMIT ?;
    """

    rows = conn.execute(
        query,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# =========================================================
# TEST / DEBUG
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("RETAIL ANALYTICS TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. Stock-out
    # -----------------------------------------------------

    stockout_items = get_stockout_risks()

    print("\n1. STOCK-OUT RISKS")
    print("-" * 60)

    print(
        f"Returned candidates: {len(stockout_items)}"
    )

    for item in stockout_items[:5]:

        print(
            f"{item['store_name']} | "
            f"{item['product_name']} | "
            f"Stock={item['closing_stock']} | "
            f"Reorder={item['reorder_level']} | "
            f"Days={item['days_of_stock']} | "
            f"Risk={item['risk_level']} | "
            f"Score={item['risk_score']}"
        )

    # -----------------------------------------------------
    # 2. Overstock
    # -----------------------------------------------------

    overstock_items = get_overstock_items()

    print("\n2. OVERSTOCK")
    print("-" * 60)

    print(
        f"Returned candidates: {len(overstock_items)}"
    )

    for item in overstock_items[:5]:

        print(
            f"{item['store_name']} | "
            f"{item['product_name']} | "
            f"Stock={item['closing_stock']} | "
            f"Target={item['target_stock']} | "
            f"Days={item['days_of_stock']}"
        )

    # -----------------------------------------------------
    # 3. Non-moving
    # -----------------------------------------------------

    non_moving_items = get_non_moving_items()

    print("\n3. NON-MOVING STOCK")
    print("-" * 60)

    print(
        f"Returned candidates: {len(non_moving_items)}"
    )

    for item in non_moving_items[:5]:

        print(
            f"{item['store_name']} | "
            f"{item['product_name']} | "
            f"Stock={item['closing_stock']} | "
            f"Sales30d={item['units_sold_30d']}"
        )

    # -----------------------------------------------------
    # 4. Sales spikes
    # -----------------------------------------------------

    spike_items = get_sales_spikes()

    print("\n4. SALES SPIKES")
    print("-" * 60)

    print(
        f"Returned candidates: {len(spike_items)}"
    )

    for item in spike_items[:5]:

        print(
            f"{item['store_name']} | "
            f"{item['product_name']} | "
            f"Recent={item['recent_daily_sales']} | "
            f"Baseline={item['baseline_daily_sales']} | "
            f"Ratio={item['spike_ratio']}"
        )

    # -----------------------------------------------------
    # 5. Sales drops
    # -----------------------------------------------------

    drop_items = get_sales_drops()

    print("\n5. SALES DROPS")
    print("-" * 60)

    print(
        f"Returned candidates: {len(drop_items)}"
    )

    for item in drop_items[:5]:

        print(
            f"{item['store_name']} | "
            f"{item['product_name']} | "
            f"Recent={item['recent_daily_sales']} | "
            f"Baseline={item['baseline_daily_sales']} | "
            f"Decline={item['decline_percentage']}%"
        )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("ANALYTICS SUMMARY")
    print("=" * 60)

    print(
        f"Stock-out risks : {len(stockout_items)}"
    )

    print(
        f"Overstock items : {len(overstock_items)}"
    )

    print(
        f"Non-moving     : {len(non_moving_items)}"
    )

    print(
        f"Sales spikes   : {len(spike_items)}"
    )

    print(
        f"Sales drops    : {len(drop_items)}"
    )

    print("=" * 60)