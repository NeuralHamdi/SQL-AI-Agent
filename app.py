
import os
import json
import re
import streamlit as st
import pandas as pd

from dotenv import load_dotenv

from agent import agent
from tools.sql_tools import executer_sql
from tools.chart_tool import tracer_graphique


# ==========================================
# 1. CONFIGURATION
# ==========================================

load_dotenv()

DEFAULT_DEMO = (
    os.getenv("DEMO_MODE", "false").lower() == "true"
)

st.set_page_config(
    page_title="SQL AI Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 2. STYLE CSS
# ==========================================

st.markdown("""
<style>

    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 650 !important;
    }

    p, label {
        color: #CBD5E1;
    }

    [data-testid="stSidebar"] {
        background-color: #111C30;
        border-right: 1px solid #26364D;
    }

    [data-testid="stMetric"] {
        background-color: #17263B;
        border: 1px solid #263B56;
        padding: 20px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #A8BCD2 !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #263B56;
        border-radius: 10px;
    }

    .stButton > button {
        background-color: #2563EB;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
    }

    .stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
    }

    hr {
        border-color: #263B56;
    }

    [data-testid="stChatInput"] {
        border-color: #334155;
    }

    .subtitle {
        color: #94A3B8;
        font-size: 14px;
    }

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. FONCTIONS UTILITAIRES
# ==========================================

def extraire_contenu(message):
    """
    Récupérer le contenu d'un ToolMessage.
    Convertir le JSON en objet Python si nécessaire.
    """

    contenu = message.content

    if isinstance(contenu, str):

        try:
            return json.loads(contenu)

        except json.JSONDecodeError:
            return contenu

    return contenu


def normaliser_reponse(contenu):
    """
    Transformer la réponse Gemini en texte
    et supprimer les images Markdown.
    """

    if isinstance(contenu, str):
        texte = contenu

    elif isinstance(contenu, list):

        textes = []

        for element in contenu:

            if isinstance(element, dict):

                if "text" in element:
                    textes.append(element["text"])

            elif isinstance(element, str):
                textes.append(element)

        texte = "\n".join(textes)

    else:
        texte = str(contenu)

    # Supprimer les images Markdown de Gemini
    texte = re.sub(
        r'!\[[^\]]*\]\([^)]+\)',
        '',
        texte
    )
    texte = re.sub(
        r'Voici le graphique correspondant\s*:?',
        '',
        texte,
        flags=re.IGNORECASE
    )

    return texte.strip()


# ==========================================
# 4. MODE DEMO : REQUETES SQL
# ==========================================

def charger_dashboard_demo():
    """
    Récupérer les indicateurs et les revenus
    directement depuis Chinook.
    """

    requete = """
        SELECT
            BillingCountry AS Pays,

            COUNT(InvoiceId) AS Nombre_factures,

            COUNT(DISTINCT CustomerId) AS Nombre_clients,

            ROUND(SUM(Total), 2) AS Chiffre_affaires,

            ROUND(AVG(Total), 2) AS Panier_moyen,

            ROUND(
                100.0 * SUM(Total) /
                (SELECT SUM(Total) FROM Invoice),
                2
            ) AS Part_du_CA_pct

        FROM Invoice

        GROUP BY BillingCountry

        ORDER BY Chiffre_affaires DESC
    """

    donnees = executer_sql(requete)

    df = pd.DataFrame(donnees)

    requete_kpi = """
        SELECT
            ROUND(SUM(Total), 2) AS chiffre_affaires,

            COUNT(InvoiceId) AS nombre_factures,

            COUNT(DISTINCT BillingCountry) AS nombre_pays,

            COUNT(DISTINCT CustomerId) AS nombre_clients

        FROM Invoice
    """

    kpi = executer_sql(requete_kpi)[0]

    return df, kpi


# ==========================================
# 5. EXTRACTION DES RESULTATS LANGGRAPH
# ==========================================

def extraire_resultats_agent(messages):
    """
    Récupérer les résultats SQL et graphiques
    retournés par les outils LangGraph.
    """

    df = None
    chart_path = None
    erreur = None

    for message in messages:

        # Identifier les ToolMessage
        if getattr(message, "type", "") != "tool":
            continue

        contenu = extraire_contenu(message)

        nom_outil = getattr(message, "name", "")

        # ==================================
        # RESULTATS SQL
        # ==================================

        if nom_outil == "executer_sql_tool":

            if isinstance(contenu, dict):

                if "erreur" in contenu:
                    erreur = contenu["erreur"]

                else:
                    df = pd.DataFrame([contenu])

            elif isinstance(contenu, list):

                if contenu:
                    df = pd.DataFrame(contenu)
                else:
                    df = pd.DataFrame()

        # ==================================
        # GRAPHIQUES
        # ==================================

        elif nom_outil == "tracer_graphique_tool":

            if isinstance(contenu, str):

                contenu = contenu.strip()

                # Vérifier si l'outil a retourné une erreur
                if contenu.startswith("Erreur"):

                    erreur = contenu

                # Vérifier si le fichier existe
                elif os.path.isfile(contenu):

                    chart_path = contenu

                    print("Graphique trouvé :", chart_path)

                else:

                    print(
                        "Graphique introuvable :",
                        contenu
                    )

    return df, chart_path, erreur


# ==========================================
# 6. AFFICHAGE DES KPI
# ==========================================

def afficher_kpi(kpi):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Chiffre d'affaires",
            f"{kpi['chiffre_affaires']:,.2f}"
        )

    with col2:
        st.metric(
            "Nombre de factures",
            f"{kpi['nombre_factures']:,}"
        )

    with col3:
        st.metric(
            "Pays",
            f"{kpi['nombre_pays']}"
        )

    with col4:
        st.metric(
            "Clients",
            f"{kpi['nombre_clients']}"
        )


# ==========================================
# 7. AFFICHAGE DYNAMIQUE DES TABLEAUX
# ==========================================

def afficher_tableau(df, key="table"):

    if df is None or df.empty:

        st.info("Aucun résultat SQL disponible.")
        return

    st.subheader("Résultats SQL")

    # Informations sur le résultat
    col1, col2 = st.columns(2)

    with col1:
        st.caption(f"{len(df)} ligne(s) retournée(s)")

    with col2:
        st.caption(f"{len(df.columns)} colonne(s)")

    # Préparer une copie pour l'affichage
    df_affichage = df.copy()

    # Rendre les noms de colonnes plus lisibles
    df_affichage.columns = [
        str(colonne).replace("_", " ").strip()
        for colonne in df_affichage.columns
    ]

    # Configuration automatique des colonnes numériques
    configurations = {}

    for colonne in df_affichage.columns:

        if pd.api.types.is_integer_dtype(df_affichage[colonne]):

            configurations[colonne] = (
                st.column_config.NumberColumn(
                    colonne,
                    format="%d"
                )
            )

        elif pd.api.types.is_float_dtype(df_affichage[colonne]):

            configurations[colonne] = (
                st.column_config.NumberColumn(
                    colonne,
                    format="%.2f"
                )
            )

    # Adapter la hauteur au nombre de lignes
    hauteur = min(
        max(120 + len(df_affichage) * 35, 120),
        450
    )

    # Afficher le tableau
    st.dataframe(
        df_affichage,
        column_config=configurations,
        use_container_width=True,
        hide_index=True,
        height=hauteur
    )

    # Export CSV
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Télécharger les résultats CSV",
        data=csv,
        file_name="resultats_sql.csv",
        mime="text/csv",
        key=f"download_{key}"
    )


# ==========================================
# 8. AFFICHAGE DES GRAPHIQUES
# ==========================================

def afficher_graphique(chart_path):

    if chart_path and os.path.isfile(chart_path):

        st.subheader("Visualisation des résultats")

        st.image(
            chart_path,
            use_container_width=True
        )

    else:
        st.info("Aucun graphique généré pour cette question.")


# ==========================================
# 9. SIDEBAR
# ==========================================

with st.sidebar:

    st.title("SQL AI Agent")

    st.caption("Natural Language to SQL")

    st.divider()

    st.subheader("Configuration")

    mode = st.radio(
        "Mode d'exécution",
        options=["DEMO", "REAL"],
        index=0 if DEFAULT_DEMO else 1
    )

    if mode == "DEMO":

        st.success(
            "Mode DEMO : SQL direct, sans Gemini."
        )

    else:

        st.info(
            "Mode REAL : Gemini et LangGraph."
        )

    st.divider()

    if st.button(
        "Nouvelle conversation",
        use_container_width=True
    ):

        st.session_state.conversation = []

        st.rerun()

    st.divider()

    st.caption("Technologies")

    st.markdown("""
    - Python
    - SQLite
    - Gemini API
    - LangChain
    - LangGraph
    - Streamlit
    - Pandas
    - Matplotlib
    """)


# ==========================================
# 10. TITRE PRINCIPAL
# ==========================================

st.title("SQL AI Agent")

st.markdown(
    '<p class="subtitle">'
    'Interrogez et analysez vos données avec le langage naturel.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# ==========================================
# 11. INITIALISER L'HISTORIQUE
# ==========================================

if "conversation" not in st.session_state:

    st.session_state.conversation = []


# ==========================================
# 12. DASHBOARD DEMO
# ==========================================

if mode == "DEMO":

    try:

        df_demo, kpi_demo = charger_dashboard_demo()

        st.subheader("Vue globale")

        afficher_kpi(kpi_demo)

        st.divider()

        afficher_tableau(
            df_demo,
            key="dashboard_demo"
        )

        st.divider()

        # Graphique du Top 10
        top10 = df_demo.head(10).to_dict("records")

        chart_path = tracer_graphique(
            top10,
            colonne_x="Pays",
            colonne_y="Chiffre_affaires"
        )

        afficher_graphique(chart_path)

    except Exception as e:

        st.error(
            f"Erreur du dashboard DEMO : {e}"
        )


# ==========================================
# 13. HISTORIQUE DE CONVERSATION
# ==========================================

st.divider()

st.subheader("Assistant conversationnel")

for i, element in enumerate(st.session_state.conversation):

    with st.chat_message(element["role"]):

        st.markdown(element["content"])

        if element["role"] == "assistant":

            # Afficher les résultats SQL
            if element.get("df") is not None:

                afficher_tableau(
                    element["df"],
                    key=f"history_{i}"
                )

            # Afficher le graphique
            if element.get("chart_path"):

                afficher_graphique(
                    element["chart_path"]
                )

            # Afficher les erreurs
            if element.get("error"):

                st.error(element["error"])


# ==========================================
# 14. SAISIE UTILISATEUR
# ==========================================

question = st.chat_input(
    "Posez une question sur vos données..."
)


# ==========================================
# 15. TRAITEMENT DE LA QUESTION
# ==========================================

if question:

    # Enregistrer la question
    st.session_state.conversation.append({

        "role": "user",
        "content": question

    })

    reponse = ""
    df_resultat = None
    chart_path = None
    erreur = None

    with st.spinner("Analyse de votre question..."):

        try:

            if mode == "DEMO":

                reponse = (
                    "Le mode DEMO utilise des requêtes SQL "
                    "prédéfinies sur la base Chinook. "
                    "Le dashboard présente les revenus par pays."
                )

            else:

                # Appeler l'agent LangGraph
                result = agent.invoke({

                    "messages": [

                        {
                            "role": "user",
                            "content": question
                        }

                    ]

                })

                messages = result["messages"]

                # Récupérer la réponse finale
                reponse = normaliser_reponse(
                    messages[-1].content
                )

                # Récupérer les résultats des outils
                df_resultat, chart_path, erreur = (
                    extraire_resultats_agent(messages)
                )

        except Exception as e:

            erreur = str(e)

            reponse = (
                "Une erreur est survenue pendant "
                "le traitement de votre question."
            )

    # Enregistrer la réponse et les résultats
    st.session_state.conversation.append({

        "role": "assistant",
        "content": reponse,
        "df": df_resultat,
        "chart_path": chart_path,
        "error": erreur

    })

    # Rafraîchir l'interface
    st.rerun()
