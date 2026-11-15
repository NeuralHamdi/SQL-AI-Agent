
import sqlite3
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent / "chinook.db"


def get_connection():
    """Créer une connexion à SQLite."""
    return sqlite3.connect(DB_PATH)


def explore_database():
    """Afficher les tables, leurs colonnes et leurs nombres de lignes."""

    connection = get_connection()
    cursor = connection.cursor()

    # Récupérer les tables de la base
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    print("\n===== TABLES DE CHINOOK =====")

    for (table_name,) in tables:

        print(f"\nTable : {table_name}")

        # Récupérer les colonnes de la table
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = cursor.fetchall()

        for column in columns:
            print(f"  - {column[1]} ({column[2]})")

        # Compter les lignes
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]

        print(f"  Nombre de lignes : {count}")

    connection.close()


if __name__ == "__main__":
    explore_database()
