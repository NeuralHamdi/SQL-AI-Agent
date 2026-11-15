
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite"
).strip()


# Vérifier que la clé existe
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY est introuvable dans .env")
