import sqlite3

conn = sqlite3.connect("file:ecommerce.db?mode=ro", uri=True)
try:
    conn.execute("DELETE FROM customers")
    print("DANGER: delete worked")
except sqlite3.OperationalError as e:
    print("Protected by read-only mode:", e)
conn.close()