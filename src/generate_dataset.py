"""
PS03 - Retail Sales & Inventory Copilot
Synthetic Dataset Generator

Purpose:
- Generate realistic retail sales + inventory data
- Deliberately create important PS03 scenarios
- Keep sales/inventory mathematically consistent
- Create a reproducible SQLite database
- Validate the dataset before saving

Run from project root:
    python src/generate_dataset.py
"""

import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42
random.seed(SEED)

NUM_STORES = 5
NUM_PRODUCTS = 100
NUM_DAYS = 90

START_DATE = date(2026, 6, 1)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "retail.db"


# ============================================================
# MASTER DATA
# ============================================================

STORES = [
    ("S001", "Hyderabad Central", "Hyderabad", "Medium"),
    ("S002", "Banjara Hills Store", "Hyderabad", "Small"),
    ("S003", "Bangalore Central", "Bangalore", "Medium"),
    ("S004", "Koramangala Store", "Bangalore", "Small"),
    ("S005", "Delhi Market Store", "Delhi", "Medium"),
]


PRODUCT_CATALOG = [
    # category, subcategory, product names
    (
        "Grocery",
        "Beverages",
        [
            "Arabica Coffee 500g",
            "Classic Tea 250g",
            "Green Tea 100g",
            "Mango Juice 1L",
            "Orange Juice 1L",
            "Instant Coffee 200g",
            "Cold Coffee 500ml",
            "Lemon Drink 750ml",
            "Mineral Water 1L",
            "Coconut Water 500ml",
        ],
    ),
    (
        "Grocery",
        "Snacks",
        [
            "Salted Potato Chips",
            "Masala Chips",
            "Butter Cookies",
            "Chocolate Cookies",
            "Roasted Peanuts",
            "Mixed Nuts 200g",
            "Granola Bar",
            "Corn Snacks",
            "Nacho Chips",
            "Fruit Bar",
        ],
    ),
    (
        "Grocery",
        "Staples",
        [
            "Basmati Rice 5kg",
            "Wheat Flour 5kg",
            "Toor Dal 1kg",
            "Moong Dal 1kg",
            "Sugar 2kg",
            "Salt 1kg",
            "Cooking Oil 1L",
            "Oats 1kg",
            "Poha 1kg",
            "Rava 1kg",
        ],
    ),
    (
        "Home & Kitchen",
        "Kitchen",
        [
            "Stainless Steel Bottle",
            "Non Stick Frying Pan",
            "Kitchen Storage Box",
            "Glass Food Container",
            "Steel Lunch Box",
            "Measuring Cup Set",
            "Kitchen Knife Set",
            "Spice Rack",
            "Cutlery Set",
            "Silicone Spatula",
        ],
    ),
    (
        "Home & Kitchen",
        "Home",
        [
            "Cotton Bedsheet",
            "Bath Towel",
            "Hand Towel Set",
            "Table Mat Set",
            "Laundry Basket",
            "Storage Basket",
            "Cushion Cover",
            "Floor Mat",
            "Curtain Panel",
            "Laundry Bag",
        ],
    ),
    (
        "Personal Care",
        "Hygiene",
        [
            "Hand Wash 250ml",
            "Body Wash 250ml",
            "Shampoo 340ml",
            "Conditioner 180ml",
            "Toothpaste 150g",
            "Toothbrush Pack",
            "Face Wash 100ml",
            "Hand Sanitizer 250ml",
            "Body Lotion 200ml",
            "Bath Soap Pack",
        ],
    ),
    (
        "Beauty",
        "Skincare",
        [
            "Moisturizer 100ml",
            "Sunscreen SPF 50",
            "Aloe Vera Gel",
            "Face Serum 30ml",
            "Lip Balm",
            "Face Mask Pack",
            "Cleansing Foam",
            "Night Cream",
            "Eye Gel",
            "Rose Water",
        ],
    ),
    (
        "Electronics",
        "Accessories",
        [
            "Wireless Earbuds",
            "USB-C Cable",
            "Fast Charger",
            "Power Bank 10000mAh",
            "Wireless Mouse",
            "Keyboard",
            "Phone Stand",
            "Laptop Sleeve",
            "Bluetooth Speaker",
            "HDMI Cable",
        ],
    ),
    (
        "Sports",
        "Fitness",
        [
            "Yoga Mat",
            "Resistance Band",
            "Skipping Rope",
            "Water Bottle Sports",
            "Dumbbell 5kg",
            "Exercise Ball",
            "Gym Gloves",
            "Fitness Towel",
            "Foam Roller",
            "Wrist Support",
        ],
    ),
    (
        "Books & Toys",
        "Books & Games",
        [
            "Children Story Book",
            "Puzzle Book",
            "Notebook Set",
            "Drawing Book",
            "Board Game",
            "Educational Puzzle",
            "Building Blocks",
            "Coloring Set",
            "Activity Book",
            "Strategy Game",
        ],
    ),
]


SUPPLIERS = [
    "FreshMart Supplies",
    "Metro Wholesale",
    "Prime Retail Distributors",
    "ValueHub Suppliers",
    "Urban Goods Supply",
    "National Retail Supply",
    "DailyNeeds Wholesale",
    "SmartChoice Distributors",
]


# ============================================================
# SCENARIO CONFIGURATION
# ============================================================

SCENARIO_COUNT = {
    "stockout": 8,
    "overstock": 6,
    "non_moving": 5,
    "spike": 7,
    "drop": 6,
    "promotion": 12,
    "supplier_delay": 5,
    "new_product": 4,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def daterange():
    for i in range(NUM_DAYS):
        yield START_DATE + timedelta(days=i)


def clamp(value, low, high):
    return max(low, min(high, value))


def money(value):
    return round(value, 2)


def choose_price(category):
    ranges = {
        "Grocery": (30, 800),
        "Home & Kitchen": (150, 1800),
        "Personal Care": (50, 600),
        "Beauty": (80, 900),
        "Electronics": (250, 3500),
        "Sports": (100, 1500),
        "Books & Toys": (80, 1200),
    }

    low, high = ranges[category]
    return money(random.uniform(low, high))


# ============================================================
# GENERATE STORES
# ============================================================

def generate_stores():
    return [
        {
            "store_id": row[0],
            "store_name": row[1],
            "city": row[2],
            "store_type": row[3],
        }
        for row in STORES
    ]


# ============================================================
# GENERATE PRODUCTS
# ============================================================

def generate_products():
    products = []

    product_id = 1

    for category, subcategory, names in PRODUCT_CATALOG:

        for name in names:
            unit_price = choose_price(category)

            cost_price = money(
                unit_price * random.uniform(0.55, 0.78)
            )

            # Demand velocity
            velocity = random.choices(
                ["A", "B", "C", "D"],
                weights=[20, 30, 35, 15],
                k=1,
            )[0]

            base_demand = {
                "A": random.randint(18, 28),
                "B": random.randint(10, 17),
                "C": random.randint(4, 9),
                "D": random.randint(1, 3),
            }[velocity]

            reorder_level = int(base_demand * random.uniform(2.5, 4.0))

            target_stock = int(
                reorder_level * random.uniform(2.0, 3.0)
            )

            target_stock = max(
                target_stock,
                reorder_level + 10
            )

            products.append(
                {
                    "product_id": f"P{product_id:03d}",
                    "product_name": name,
                    "category": category,
                    "subcategory": subcategory,
                    "unit_price": unit_price,
                    "cost_price": cost_price,
                    "reorder_level": reorder_level,
                    "target_stock": target_stock,
                    "supplier": random.choice(SUPPLIERS),
                    "velocity": velocity,
                    "base_demand": base_demand,
                }
            )

            product_id += 1

    return products


# ============================================================
# SCENARIO ASSIGNMENT
# ============================================================

def assign_scenarios(products, stores):
    """
    Assign scenario behavior to specific store-product pairs.

    The actual analytics engine will later discover the conditions
    from the generated numbers.
    """

    pairs = [
        (s["store_id"], p["product_id"])
        for s in stores
        for p in products
    ]

    random.shuffle(pairs)

    scenarios = {
        "stockout": [],
        "overstock": [],
        "non_moving": [],
        "spike": [],
        "drop": [],
        "promotion": [],
        "supplier_delay": [],
        "new_product": [],
    }

    used = set()

    def select_pairs(count, allowed=None):
        selected = []

        candidates = [
            pair for pair in pairs
            if pair not in used
        ]

        if allowed:
            candidates = [
                pair for pair in candidates
                if allowed(pair)
            ]

        for pair in candidates[:count]:
            selected.append(pair)
            used.add(pair)

        return selected

    scenarios["stockout"] = select_pairs(
        SCENARIO_COUNT["stockout"]
    )

    scenarios["overstock"] = select_pairs(
        SCENARIO_COUNT["overstock"]
    )

    scenarios["non_moving"] = select_pairs(
        SCENARIO_COUNT["non_moving"]
    )

    scenarios["spike"] = select_pairs(
        SCENARIO_COUNT["spike"]
    )

    scenarios["drop"] = select_pairs(
        SCENARIO_COUNT["drop"]
    )

    scenarios["promotion"] = select_pairs(
        SCENARIO_COUNT["promotion"]
    )

    scenarios["supplier_delay"] = select_pairs(
        SCENARIO_COUNT["supplier_delay"]
    )

    scenarios["new_product"] = select_pairs(
        SCENARIO_COUNT["new_product"]
    )

    return scenarios


# ============================================================
# SCENARIO LOOKUP
# ============================================================

def scenario_lookup(scenarios):
    lookup = {}

    for scenario_name, pairs in scenarios.items():
        for pair in pairs:
            lookup.setdefault(pair, set()).add(scenario_name)

    return lookup


# ============================================================
# DEMAND GENERATION
# ============================================================

def calculate_demand(product, store, current_date, scenario_names):
    base = product["base_demand"]

    # Store effect
    store_multiplier = {
        "Medium": 1.15,
        "Small": 0.85,
    }[store["store_type"]]

    # Weekend effect
    weekday = current_date.weekday()

    weekend_multiplier = {
        0: 0.92,
        1: 0.90,
        2: 0.95,
        3: 1.00,
        4: 1.08,
        5: 1.25,
        6: 1.30,
    }[weekday]

    demand = (
        base
        * store_multiplier
        * weekend_multiplier
    )

    # Normal noise
    demand *= random.uniform(0.85, 1.15)

    # -------------------------
    # Scenario modifiers
    # -------------------------

    if "stockout" in scenario_names:
        # Strong demand near end of dataset
        if current_date >= START_DATE + timedelta(days=72):
            demand *= 1.35

    if "overstock" in scenario_names:
        # Persistent low demand creates genuine excess inventory.
        demand *= 0.05

    if "non_moving" in scenario_names:
        # Product stops moving during last 35 days
        if current_date >= START_DATE + timedelta(days=55):
            demand = 0

    if "spike" in scenario_names:
        # Temporary demand surge
        if 45 <= (current_date - START_DATE).days <= 51:
            demand *= 3.0

    if "drop" in scenario_names:
        # Sharp but realistic decline
        if current_date >= START_DATE + timedelta(days=60):
            demand *= 0.30

    if "promotion" in scenario_names:
        # Promotion period
        if 50 <= (current_date - START_DATE).days <= 55:
            demand *= 2.0

    # New products have no sales before launch
    if "new_product" in scenario_names:
        if current_date < START_DATE + timedelta(days=82):
            demand = 0

    return max(0, int(round(demand)))


# ============================================================
# BUSINESS EVENTS
# ============================================================

def generate_business_events(products, stores, scenarios):
    events = []
    event_id = 1

    pair_to_product = {
        p["product_id"]: p
        for p in products
    }

    # Promotions
    for store_id, product_id in scenarios["promotion"]:
        events.append(
            {
                "event_id": event_id,
                "event_date": (
                    START_DATE + timedelta(days=50)
                ).isoformat(),
                "store_id": store_id,
                "product_id": product_id,
                "event_type": "PROMOTION",
                "description": (
                    "Weekend promotional offer increased "
                    "customer demand."
                ),
            }
        )
        event_id += 1

    # Supplier delays
    for store_id, product_id in scenarios["supplier_delay"]:
        events.append(
            {
                "event_id": event_id,
                "event_date": (
                    START_DATE + timedelta(days=72)
                ).isoformat(),
                "store_id": store_id,
                "product_id": product_id,
                "event_type": "SUPPLIER_DELAY",
                "description": (
                    "Supplier shipment delayed, "
                    "temporarily affecting replenishment."
                ),
            }
        )
        event_id += 1

    # Store-wide holidays/local events
    store_events = [
        (20, "HOLIDAY", "Festival holiday increased store traffic."),
        (44, "LOCAL_EVENT", "Local community event increased footfall."),
        (68, "HOLIDAY", "Regional holiday affected shopping demand."),
    ]

    for day_offset, event_type, description in store_events:
        for store in stores:
            events.append(
                {
                    "event_id": event_id,
                    "event_date": (
                        START_DATE + timedelta(days=day_offset)
                    ).isoformat(),
                    "store_id": store["store_id"],
                    "product_id": None,
                    "event_type": event_type,
                    "description": description,
                }
            )
            event_id += 1

    # Price changes
    selected_products = random.sample(products, 8)

    for product in selected_products:
        day_offset = random.randint(25, 65)

        events.append(
            {
                "event_id": event_id,
                "event_date": (
                    START_DATE + timedelta(days=day_offset)
                ).isoformat(),
                "store_id": None,
                "product_id": product["product_id"],
                "event_type": "PRICE_CHANGE",
                "description": (
                    "Product price adjusted as part of "
                    "routine pricing review."
                ),
            }
        )

        event_id += 1

    return events


# ============================================================
# GENERATE SALES + INVENTORY TOGETHER
# ============================================================

def generate_transactions(products, stores, scenarios):
    """
    Generate sales and inventory together.

    This is important because inventory is directly tied to
    actual units sold.
    """

    scenario_map = scenario_lookup(scenarios)

    sales = []
    inventory = []

    sale_id = 1
    inventory_id = 1

    # Current stock for each store/product
    stock = {}

    # Track whether supplier delay is active
    supplier_delay_pairs = set(scenarios["supplier_delay"])

    # Initialize stock
    for store in stores:
        for product in products:

            pair = (
                store["store_id"],
                product["product_id"],
            )

            scenario_names = scenario_map.get(pair, set())

            initial_stock = product["target_stock"]

            # Overstock deliberately begins with substantial excess stock.
            if "overstock" in scenario_names:
                initial_stock = int(
                    product["target_stock"] * 6.0
                )

            # Non-moving gets meaningful stock
            if "non_moving" in scenario_names:
                initial_stock = max(
                    30,
                    product["target_stock"]
                )

            # New product receives stock only around launch
            if "new_product" in scenario_names:
                initial_stock = 0

            stock[pair] = initial_stock

    # --------------------------------------------------------
    # Daily generation
    # --------------------------------------------------------

    for day_offset in range(NUM_DAYS):

        current_date = START_DATE + timedelta(days=day_offset)

        for store in stores:

            for product in products:

                pair = (
                    store["store_id"],
                    product["product_id"],
                )

                scenario_names = scenario_map.get(
                    pair,
                    set()
                )

                opening_stock = stock[pair]

                # --------------------------------------------
                # Stock received
                # --------------------------------------------

                received = 0

                # New product launch
                if (
                    "new_product" in scenario_names
                    and day_offset == 82
                ):
                    received = product["target_stock"]

                # Normal replenishment
                if "new_product" not in scenario_names:

                    supplier_delayed = (
                        pair in supplier_delay_pairs
                        and 72 <= day_offset <= 82
                    )

                    stockout_protection_disabled = (
                        "stockout" in scenario_names
                        and day_offset >= 72
                    )

                    overstock_replenishment_disabled = (
                        "overstock" in scenario_names
                    )

                    if (
                        opening_stock
                        <= product["reorder_level"]
                        and not supplier_delayed
                        and not stockout_protection_disabled
                        and not overstock_replenishment_disabled
                    ):
                        received = max(
                            0,
                            product["target_stock"]
                            - opening_stock
                        )

                # --------------------------------------------
                # Demand
                # --------------------------------------------

                demand = calculate_demand(
                    product,
                    store,
                    current_date,
                    scenario_names,
                )

                available_stock = (
                    opening_stock + received
                )

                # Cannot sell more than available stock
                units_sold = min(
                    demand,
                    available_stock
                )

                closing_stock = (
                    opening_stock
                    + received
                    - units_sold
                )

                # Safety assertion
                if closing_stock < 0:
                    raise ValueError(
                        "Negative inventory detected"
                    )

                # --------------------------------------------
                # Sales record
                # --------------------------------------------

                revenue = money(
                    units_sold * product["unit_price"]
                )

                sales.append(
                    {
                        "sale_id": sale_id,
                        "sale_date": current_date.isoformat(),
                        "store_id": store["store_id"],
                        "product_id": product["product_id"],
                        "units_sold": units_sold,
                        "unit_price": product["unit_price"],
                        "revenue": revenue,
                    }
                )

                sale_id += 1

                # --------------------------------------------
                # Inventory record
                # --------------------------------------------

                inventory.append(
                    {
                        "inventory_id": inventory_id,
                        "inventory_date": current_date.isoformat(),
                        "store_id": store["store_id"],
                        "product_id": product["product_id"],
                        "opening_stock": opening_stock,
                        "stock_received": received,
                        "units_sold": units_sold,
                        "closing_stock": closing_stock,
                    }
                )

                inventory_id += 1

                stock[pair] = closing_stock

    return sales, inventory


# ============================================================
# VALIDATION
# ============================================================

def validate_data(stores, products, sales, inventory, events):

    errors = []

    store_ids = {
        s["store_id"]
        for s in stores
    }

    product_ids = {
        p["product_id"]
        for p in products
    }

    # --------------------------------------------
    # Product validation
    # --------------------------------------------

    for product in products:

        if product["cost_price"] >= product["unit_price"]:
            errors.append(
                f"Invalid pricing: {product['product_id']}"
            )

        if product["reorder_level"] >= product["target_stock"]:
            errors.append(
                f"Invalid stock levels: {product['product_id']}"
            )

    # --------------------------------------------
    # Sales validation
    # --------------------------------------------

    sales_keys = set()

    for row in sales:

        if row["store_id"] not in store_ids:
            errors.append("Invalid store in sales")

        if row["product_id"] not in product_ids:
            errors.append("Invalid product in sales")

        expected_revenue = money(
            row["units_sold"] * row["unit_price"]
        )

        if row["revenue"] != expected_revenue:
            errors.append(
                f"Revenue mismatch: {row['sale_id']}"
            )

        key = (
            row["store_id"],
            row["product_id"],
            row["sale_date"],
        )

        if key in sales_keys:
            errors.append(
                f"Duplicate sales record: {key}"
            )

        sales_keys.add(key)

    # --------------------------------------------
    # Inventory validation
    # --------------------------------------------

    inventory_keys = set()

    for row in inventory:

        if row["store_id"] not in store_ids:
            errors.append("Invalid store in inventory")

        if row["product_id"] not in product_ids:
            errors.append("Invalid product in inventory")

        expected_closing = (
            row["opening_stock"]
            + row["stock_received"]
            - row["units_sold"]
        )

        if row["closing_stock"] != expected_closing:
            errors.append(
                f"Inventory equation failed: "
                f"{row['inventory_id']}"
            )

        if (
            row["opening_stock"] < 0
            or row["stock_received"] < 0
            or row["units_sold"] < 0
            or row["closing_stock"] < 0
        ):
            errors.append(
                f"Negative inventory value: "
                f"{row['inventory_id']}"
            )

        key = (
            row["store_id"],
            row["product_id"],
            row["inventory_date"],
        )

        if key in inventory_keys:
            errors.append(
                f"Duplicate inventory record: {key}"
            )

        inventory_keys.add(key)

    # --------------------------------------------
    # Event validation
    # --------------------------------------------

    for event in events:

        if (
            event["store_id"] is not None
            and event["store_id"] not in store_ids
        ):
            errors.append(
                f"Invalid event store: {event['event_id']}"
            )

        if (
            event["product_id"] is not None
            and event["product_id"] not in product_ids
        ):
            errors.append(
                f"Invalid event product: {event['event_id']}"
            )

    # --------------------------------------------
    # Expected number of records
    # --------------------------------------------

    expected_transaction_rows = (
        NUM_STORES
        * NUM_PRODUCTS
        * NUM_DAYS
    )

    if len(sales) != expected_transaction_rows:
        errors.append(
            f"Sales row count incorrect: "
            f"{len(sales)} vs {expected_transaction_rows}"
        )

    if len(inventory) != expected_transaction_rows:
        errors.append(
            f"Inventory row count incorrect: "
            f"{len(inventory)} vs {expected_transaction_rows}"
        )

    return errors


# ============================================================
# CREATE SQLITE DATABASE
# ============================================================

def create_database(stores, products, sales, inventory, events):

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Remove previous generated database
    if DB_PATH.exists():
        DB_PATH.unlink()

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    # --------------------------------------------
    # Stores
    # --------------------------------------------

    cursor.execute(
        """
        CREATE TABLE stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            store_type TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------
    # Products
    # --------------------------------------------

    cursor.execute(
        """
        CREATE TABLE products (
            product_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT NOT NULL,
            unit_price REAL NOT NULL,
            cost_price REAL NOT NULL,
            reorder_level INTEGER NOT NULL,
            target_stock INTEGER NOT NULL,
            supplier TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------
    # Sales
    # --------------------------------------------

    cursor.execute(
        """
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            sale_date TEXT NOT NULL,
            store_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            units_sold INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            revenue REAL NOT NULL,

            FOREIGN KEY (store_id)
                REFERENCES stores(store_id),

            FOREIGN KEY (product_id)
                REFERENCES products(product_id),

            UNIQUE(store_id, product_id, sale_date)
        )
        """
    )

    # --------------------------------------------
    # Inventory
    # --------------------------------------------

    cursor.execute(
        """
        CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY,
            inventory_date TEXT NOT NULL,
            store_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            opening_stock INTEGER NOT NULL,
            stock_received INTEGER NOT NULL,
            units_sold INTEGER NOT NULL,
            closing_stock INTEGER NOT NULL,

            FOREIGN KEY (store_id)
                REFERENCES stores(store_id),

            FOREIGN KEY (product_id)
                REFERENCES products(product_id),

            UNIQUE(store_id, product_id, inventory_date)
        )
        """
    )

    # --------------------------------------------
    # Business events
    # --------------------------------------------

    cursor.execute(
        """
        CREATE TABLE business_events (
            event_id INTEGER PRIMARY KEY,
            event_date TEXT NOT NULL,
            store_id TEXT,
            product_id TEXT,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,

            FOREIGN KEY (store_id)
                REFERENCES stores(store_id),

            FOREIGN KEY (product_id)
                REFERENCES products(product_id)
        )
        """
    )

    # --------------------------------------------
    # Insert stores
    # --------------------------------------------

    cursor.executemany(
        """
        INSERT INTO stores
        (store_id, store_name, city, store_type)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                s["store_id"],
                s["store_name"],
                s["city"],
                s["store_type"],
            )
            for s in stores
        ],
    )

    # --------------------------------------------
    # Insert products
    # --------------------------------------------

    cursor.executemany(
        """
        INSERT INTO products
        (
            product_id,
            product_name,
            category,
            subcategory,
            unit_price,
            cost_price,
            reorder_level,
            target_stock,
            supplier
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                p["product_id"],
                p["product_name"],
                p["category"],
                p["subcategory"],
                p["unit_price"],
                p["cost_price"],
                p["reorder_level"],
                p["target_stock"],
                p["supplier"],
            )
            for p in products
        ],
    )

    # --------------------------------------------
    # Insert sales
    # --------------------------------------------

    cursor.executemany(
        """
        INSERT INTO sales
        (
            sale_id,
            sale_date,
            store_id,
            product_id,
            units_sold,
            unit_price,
            revenue
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                s["sale_id"],
                s["sale_date"],
                s["store_id"],
                s["product_id"],
                s["units_sold"],
                s["unit_price"],
                s["revenue"],
            )
            for s in sales
        ],
    )

    # --------------------------------------------
    # Insert inventory
    # --------------------------------------------

    cursor.executemany(
        """
        INSERT INTO inventory
        (
            inventory_id,
            inventory_date,
            store_id,
            product_id,
            opening_stock,
            stock_received,
            units_sold,
            closing_stock
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                i["inventory_id"],
                i["inventory_date"],
                i["store_id"],
                i["product_id"],
                i["opening_stock"],
                i["stock_received"],
                i["units_sold"],
                i["closing_stock"],
            )
            for i in inventory
        ],
    )

    # --------------------------------------------
    # Insert events
    # --------------------------------------------

    cursor.executemany(
        """
        INSERT INTO business_events
        (
            event_id,
            event_date,
            store_id,
            product_id,
            event_type,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                e["event_id"],
                e["event_date"],
                e["store_id"],
                e["product_id"],
                e["event_type"],
                e["description"],
            )
            for e in events
        ],
    )

    # --------------------------------------------
    # Indexes
    # --------------------------------------------

    indexes = [
        "CREATE INDEX idx_sales_date ON sales(sale_date)",
        "CREATE INDEX idx_sales_store ON sales(store_id)",
        "CREATE INDEX idx_sales_product ON sales(product_id)",
        """
        CREATE INDEX idx_sales_store_product_date
        ON sales(store_id, product_id, sale_date)
        """,
        "CREATE INDEX idx_inventory_date ON inventory(inventory_date)",
        "CREATE INDEX idx_inventory_store ON inventory(store_id)",
        "CREATE INDEX idx_inventory_product ON inventory(product_id)",
        """
        CREATE INDEX idx_inventory_store_product_date
        ON inventory(store_id, product_id, inventory_date)
        """,
        "CREATE INDEX idx_events_date ON business_events(event_date)",
        "CREATE INDEX idx_events_store ON business_events(store_id)",
        "CREATE INDEX idx_events_product ON business_events(product_id)",
        "CREATE INDEX idx_events_type ON business_events(event_type)",
        "CREATE INDEX idx_products_category ON products(category)",
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    connection.commit()
    connection.close()


# ============================================================
# DATASET REPORT
# ============================================================

def print_report(
    stores,
    products,
    sales,
    inventory,
    events,
):
    total_revenue = sum(
        row["revenue"]
        for row in sales
    )

    categories = len(
        set(p["category"] for p in products)
    )

    print()
    print("=" * 70)
    print("PS03 RETAIL DATASET")
    print("=" * 70)

    print(f"Stores              : {len(stores)}")
    print(f"Products            : {len(products)}")
    print(f"Categories          : {categories}")
    print(f"Days                : {NUM_DAYS}")
    print(f"Start date          : {START_DATE}")
    print(
        f"End date            : "
        f"{START_DATE + timedelta(days=NUM_DAYS - 1)}"
    )

    print()
    print("TABLES")
    print("-" * 70)

    print(f"stores              : {len(stores):,}")
    print(f"products            : {len(products):,}")
    print(f"sales               : {len(sales):,}")
    print(f"inventory           : {len(inventory):,}")
    print(f"business_events     : {len(events):,}")

    print()
    print("REVENUE")
    print("-" * 70)

    print(f"Total revenue       : ₹{total_revenue:,.2f}")

    print()
    print("DATABASE")
    print("-" * 70)

    print(f"Created             : {DB_PATH}")

    print()
    print("=" * 70)
    print("DATASET GENERATION SUCCESSFUL")
    print("=" * 70)
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("Generating PS03 retail dataset...")
    print(f"Random seed: {SEED}")

    stores = generate_stores()

    products = generate_products()

    scenarios = assign_scenarios(
        products,
        stores,
    )

    sales, inventory = generate_transactions(
        products,
        stores,
        scenarios,
    )

    events = generate_business_events(
        products,
        stores,
        scenarios,
    )

    print("Running validation...")

    errors = validate_data(
        stores,
        products,
        sales,
        inventory,
        events,
    )

    if errors:

        print()
        print("DATASET VALIDATION FAILED")
        print("-" * 70)

        for error in errors[:20]:
            print("ERROR:", error)

        if len(errors) > 20:
            print(
                f"... and {len(errors) - 20} more errors"
            )

        raise SystemExit(1)

    print("Validation passed.")

    create_database(
        stores,
        products,
        sales,
        inventory,
        events,
    )

    print_report(
        stores,
        products,
        sales,
        inventory,
        events,
    )


if __name__ == "__main__":
    main()