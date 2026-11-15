import sqlite3
from pathlib import Path
DB_path=Path(__file__).parent/'chinook.db'
conn=sqlite3.connect(DB_path)
query1 = """
SELECT FirstName, LastName, Country
FROM Customer
LIMIT 5;
"""
query2 = """
SELECT BillingCountry, SUM(Total) AS revenue
FROM Invoice
GROUP BY BillingCountry
ORDER BY revenue DESC
LIMIT 5;
"""
for i ,q in enumerate([query1,query2]):
    print(f"Query {i+1}:")
    ex=conn.execute(q)

    print(ex.fetchall())
conn.close()