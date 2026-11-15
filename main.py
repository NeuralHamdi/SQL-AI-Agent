
import sqlite3

conn=sqlite3.connect(':memory:')

print("conexion exitosa")
conn.close()