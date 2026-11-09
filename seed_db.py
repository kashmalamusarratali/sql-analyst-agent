import sqlite3
import random
from faker import Faker
from datetime import datetime , timedelta

fake = Faker()
random.seed(42)
conn = sqlite3.connect("ecommerce.db")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS returns;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers(
id INTEGER PRIMARY KEY,
name TEXT,
country TEXT,
signup_date TEXT
);

CREATE TABLE products(
id INTEGER PRIMARY KEY,
name TEXT,
category TEXT,
price REAL
);

CREATE TABLE orders(
id INTEGER PRIMARY KEY,
customer_id INTEGER,
order_date TEXT,
status TEXT,
FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items(
id INTEGER PRIMARY KEY,
order_id INTEGER,
product_id INTEGER,
quantity INTEGER,
FOREIGN KEY (order_id) REFERENCES orders(id),
FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE TABLE returns(
id INTEGER PRIMARY KEY,
order_id INTEGER,
reason TEXT,
refund_amount REAL,
FOREIGN KEY (order_id) REFERENCES orders(id)
);

""")

countries = ["USA", "UK", "UAE", "Germany", "Canada", "Saudi Arabia"]

# customers

for i in range(1, 1001):
    signup = fake.date_between(start_date="-2y", end_date="today").isoformat()
    cur.execute(
        "INSERT INTO customers (id, name, country, signup_date) VALUES (?, ?, ?, ?)",
        (i, fake.name(), random.choice(countries), signup),
    )

# products
categories = {
    "Electronics": (20, 500),
    "Clothing": (10, 120),
    "Home": (15, 300),
    "Beauty": (5, 80),
    "Sports": (10, 250),
}

pid = 1
for category, (low, high) in categories.items():
    for _ in range(40):
        cur.execute(
            "INSERT INTO products (id, name, category, price) VALUES (?, ?, ?, ?)",
            (pid, f"{fake.word().title()} {category} Item", category, round(random.uniform(low, high), 2)),
        )
        pid += 1


# load prices so we can calculate order totals
cur.execute("SELECT id, price FROM products")
prices = dict(cur.fetchall())

statuses = ["delivered", "shipped", "cancelled", "returned"]
weights = [70, 10, 8, 12]
reasons = ["Damaged", "Wrong item", "Not as described", "Changed mind", "Late delivery"]

item_id = 1
return_id = 1

for order_id in range(1, 5001):
    customer_id = random.randint(1, 1000)
    order_date = fake.date_between(start_date="-1y", end_date="today").isoformat()
    status = random.choices(statuses, weights=weights)[0]

    cur.execute(
        "INSERT INTO orders (id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
        (order_id, customer_id, order_date, status),
    )

    total = 0
    for _ in range(random.randint(1, 4)):
        product_id = random.randint(1, 200)
        qty = random.randint(1, 3)
        cur.execute(
            "INSERT INTO order_items (id, order_id, product_id, quantity) VALUES (?, ?, ?, ?)",
            (item_id, order_id, product_id, qty),
        )
        item_id += 1
        total += prices[product_id] * qty

    if status == "returned":
        cur.execute(
            "INSERT INTO returns (id, order_id, reason, refund_amount) VALUES (?, ?, ?, ?)",
            (return_id, order_id, random.choice(reasons), round(total, 2)),
        )
        return_id += 1

        


conn.commit()
conn.close()
print("Table Created")
