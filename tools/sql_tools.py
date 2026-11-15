
import sqlite3
from pathlib import Path


# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "database" / "chinook.db"

# Nombre maximum de résultats
MAX_ROWS = 50


def get_connection():
    """Ouvrir une connexion SQLite en lecture seule."""

    database_uri = f"{DB_PATH.as_uri()}?mode=ro"

    return sqlite3.connect(database_uri, uri=True)


def lister_tables():
    """Lister les tables et leurs colonnes."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cursor.fetchall()

        schema = {}

        for table in tables:
            table_name = table[0]

            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()

            schema[table_name] = [
                column[1] for column in columns
            ]

        return schema

    finally:
        connection.close()


def executer_sql(requete: str):
    """Exécuter uniquement des requêtes SELECT avec un maximum de 50 lignes."""

    # 1. Vérifier que la requête n'est pas vide
    requete = requete.strip()

    if not requete:
        raise ValueError("La requête SQL est vide.")

    # 2. Autoriser uniquement les requêtes SELECT
    if not requete.upper().startswith("SELECT"):
        raise ValueError(
            "Sécurité : seules les requêtes SELECT sont autorisées."
        )

    # 3. Retirer le point-virgule final s'il existe
    requete = requete.rstrip().rstrip(";")

    # 4. Limiter les résultats à 50 lignes
    requete_limitee = f"""
        SELECT *
        FROM ({requete}) AS resultat
        LIMIT {MAX_ROWS}
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # 5. Exécuter la requête sécurisée
        cursor.execute(requete_limitee)

        # Récupérer les noms des colonnes
        colonnes = [
            description[0]
            for description in cursor.description
        ]

        # Récupérer les résultats
        lignes = cursor.fetchall()

        # Transformer les résultats en dictionnaires
        resultats = [
            dict(zip(colonnes, ligne))
            for ligne in lignes
        ]

        return resultats

    finally:
        connection.close()
