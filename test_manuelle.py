
from tools.sql_tools import executer_sql


# Test 1 : SELECT autorisé
print("Test SELECT :")
print(executer_sql("SELECT * FROM Customer LIMIT 3"))


# Test 2 : DELETE interdit
print("\nTest DELETE :")

try:
    executer_sql("DELETE FROM Customer")
except Exception as e:
    print("Bloqué :", e)


# Test 3 : DROP interdit
print("\nTest DROP :")

try:
    executer_sql("DROP TABLE Customer")
except Exception as e:
    print("Bloqué :", e)


# Test 4 : maximum 50 résultats
print("\nTest limite :")
resultats = executer_sql("SELECT * FROM Track")

print("Nombre de lignes :", len(resultats))
