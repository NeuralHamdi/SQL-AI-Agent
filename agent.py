import streamlit as st

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from config import GOOGLE_API_KEY, GEMINI_MODEL
from tools.sql_tools import lister_tables, executer_sql
from tools.chart_tool import tracer_graphique


# ==========================================
# 1. INITIALISER GEMINI
# ==========================================
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
    timeout=600,
    max_retries=2
)
# ==========================================
# 2. TRANSFORMER LES FONCTIONS EN OUTILS
# ==========================================

@tool
def lister_tables_tool() -> dict:
    """
    Découvrir les tables et les colonnes
    disponibles dans la base Chinook.
    """
    return lister_tables()


@tool
def executer_sql_tool(requete: str):
    """
    Exécuter une requête SQL SELECT
    sur la base Chinook.
    """
    try:
        return executer_sql(requete)

    except Exception as e:
        return {
            "erreur": str(e),
            "instruction": "Corrige la requête SQL et réessaie."
        }


@tool
def tracer_graphique_tool(
    requete: str,
    colonne_x: str,
    colonne_y: str
) -> str:
    """
    Créer un graphique à partir d'une requête SQL.

    requete : requête SQL SELECT à exécuter.
    colonne_x : colonne utilisée pour l'axe des catégories.
    colonne_y : colonne numérique utilisée pour les valeurs.

    Retourne le chemin exact du graphique généré.
    """

    try:
        # 1. Exécuter la requête SQL
        donnees = executer_sql(requete)

        # 2. Vérifier les résultats
        if not donnees:
            return "Erreur : aucune donnée disponible pour le graphique."

        # 3. Générer le graphique
        chemin = tracer_graphique(
            donnees,
            colonne_x,
            colonne_y
        )

        # 4. Retourner uniquement le chemin
        return chemin

    except Exception as e:
        return f"Erreur lors de la création du graphique : {str(e)}"


# ==========================================
# 3. DONNER LES OUTILS À GEMINI
# ==========================================

tools = [
    lister_tables_tool,
    executer_sql_tool,
    tracer_graphique_tool
]

llm_with_tools = llm.bind_tools(tools)


# ==========================================
# 4. CRÉER LE NŒUD CHATBOT
# ==========================================

def chatbot(state: MessagesState):

    system_message = SystemMessage(
        content="""
        Tu es un assistant intelligent qui répond aux questions
        concernant la base de données Chinook.

        RÈGLES :

        1. Utilise lister_tables_tool pour découvrir les tables
           et leurs colonnes si nécessaire.

        2. Utilise executer_sql_tool pour répondre aux questions
           avec des données SQL.

        3. Utilise uniquement des requêtes de lecture SQL.

        4. Utilise tracer_graphique_tool UNIQUEMENT si
           l'utilisateur demande un graphique.

        5. Pour créer un graphique, transmets une requête SQL
           ainsi que les noms des colonnes X et Y.

        6. Ne demande jamais à tracer un graphique si
           l'utilisateur demande seulement une réponse textuelle.

      7. Présente les résultats clairement, dans la même langue
   que celle utilisée par l'utilisateur dans sa question
   (français, anglais, arabe, etc.).
        """
    )

    messages = [system_message] + state["messages"]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


# ==========================================
# 5. CONSTRUIRE LE WORKFLOW LANGGRAPH
# ==========================================

builder = StateGraph(MessagesState)

# Ajouter les nœuds
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))

# Définir le début du workflow
builder.add_edge(START, "chatbot")

# Vérifier si Gemini demande un outil
builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

# Retourner au chatbot après l'exécution d'un outil
builder.add_edge("tools", "chatbot")


# ==========================================
# 6. COMPILER LE WORKFLOW
# ==========================================

agent = builder.compile()


# ==========================================
# 7. TESTER L'AGENT
# ==========================================

if __name__ == "__main__":

    question = """
    Crée un graphique en barres représentant
    les revenus par pays dans Chinook.

    Utilise les données SQL pour créer le graphique.
    """

    result = agent.invoke({
        "messages": [
            HumanMessage(content=question)
        ]
    })

    st.write("========== DEBUG LANGGRAPH ==========")

    for i, message in enumerate(result["messages"]):

        st.write(f"Message {i + 1}")
        st.write("TYPE :", type(message).__name__)
        st.write("CONTENT :", message.content)

        if hasattr(message, "tool_calls"):
            st.write("TOOL CALLS :", message.tool_calls)

        if hasattr(message, "name"):
            st.write("TOOL NAME :", message.name)

        st.divider()

    st.write("========== RÉPONSE FINALE ==========")
    st.write(result["messages"][-1].content)