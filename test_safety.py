from agent import validate_sql

tests = [
    "SELECT * FROM customers",
    "DROP TABLE customers",
    "DELETE FROM orders WHERE id = 1",
    "SELECT * FROM customers; DROP TABLE orders",
    "UPDATE products SET price = 0",
]

for sql in tests:
    try:
        validate_sql(sql)
        print("ALLOWED:", sql)
    except ValueError as e:
        print("BLOCKED:", sql, "->", e)