
from tools.sql_tools import lister_tables, executer_sql


# Test 1 : découvrir les tables
tables = lister_tables()

print("===== TABLES =====")

for table, columns in tables.items():
    print(table, ":", columns)


# Test 2 : exécuter une requête SQL
print("\n===== TOP 5 CLIENTS =====")

results = executer_sql("""
    SELECT FirstName, LastName, Country
    FROM Customer
    LIMIT 5
""")

for result in results:
    print(result)
