
import pytest

from tools.sql_tools import executer_sql


def test_select_autorise():
    """Vérifier qu'une requête SELECT fonctionne."""

    resultats = executer_sql(
        "SELECT * FROM Customer LIMIT 3"
    )

    assert len(resultats) == 3


def test_delete_interdit():
    """Vérifier que DELETE est refusé."""

    with pytest.raises(ValueError):
        executer_sql("DELETE FROM Customer")


def test_drop_interdit():
    """Vérifier que DROP est refusé."""

    with pytest.raises(ValueError):
        executer_sql("DROP TABLE Customer")


def test_limite_50_lignes():
    """Vérifier que le résultat ne dépasse pas 50 lignes."""

    resultats = executer_sql("SELECT * FROM Customer")

    assert len(resultats) <= 50
