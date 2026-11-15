import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path
import uuid


# Dossier de sauvegarde des graphiques
CHART_DIR = Path(__file__).parent.parent / "generated" / "charts"


def tracer_graphique(donnees, colonne_x, colonne_y):
    """
    Générer un graphique horizontal professionnel
    à partir des résultats SQL.
    """

    if not donnees:
        raise ValueError("Aucune donnée à afficher.")

    # Vérifier les colonnes
    if colonne_x not in donnees[0] or colonne_y not in donnees[0]:
        raise ValueError("Colonne introuvable.")

    # Préparer les données
    labels = [str(row[colonne_x]) for row in donnees]
    valeurs = [float(row[colonne_y]) for row in donnees]

    # Créer la figure
    fig, ax = plt.subplots(figsize=(11, 6))

    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Palette professionnelle
    couleur_principale = "#2563EB"
    couleur_secondaire = "#14B8A6"

    couleurs = [
        couleur_secondaire if i == 0 else couleur_principale
        for i in range(len(labels))
    ]

    # Graphique horizontal
    positions = range(len(labels))

    barres = ax.barh(
        positions,
        valeurs,
        color=couleurs,
        height=0.65
    )

    ax.set_yticks(list(positions))
    ax.set_yticklabels(labels, fontsize=10)

    # Le premier élément apparaît en haut
    ax.invert_yaxis()

    # Afficher les valeurs
    ax.bar_label(
        barres,
        fmt="%.2f",
        padding=6,
        fontsize=9,
        color="#334155"
    )

    # Titres
    ax.set_title(
        f"{colonne_y} par {colonne_x}",
        fontsize=15,
        fontweight="bold",
        color="#0F172A",
        pad=20
    )

    ax.set_xlabel(
        colonne_y,
        fontsize=10,
        color="#475569"
    )

    # Style des axes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_color("#E2E8F0")

    ax.tick_params(axis="both", colors="#475569")
    ax.tick_params(axis="y", length=0)

    # Grille discrète
    ax.xaxis.grid(
        True,
        linestyle="--",
        alpha=0.25
    )

    ax.set_axisbelow(True)

    # Espacement
    fig.tight_layout()

    # Créer le dossier
    CHART_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Nom unique pour ne pas écraser les anciens graphiques
    chart_path = CHART_DIR / f"chart_{uuid.uuid4().hex[:10]}.png"

    # Sauvegarder
    fig.savefig(
        chart_path,
        dpi=160,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close(fig)

    return str(chart_path)