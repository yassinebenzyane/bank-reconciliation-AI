"""Tests règles déterministes de classification (J3)."""
import pytest


@pytest.mark.skip(reason="J3")
def test_urssaf_rule():
    """type_op=08 + libellé contient URSSAF → Charges sociales."""
    pass


@pytest.mark.skip(reason="J3")
def test_dgfip_rule():
    """type_op=08 + DGFIP → TVA."""
    pass


@pytest.mark.skip(reason="J3")
def test_pret_rule():
    """type_op=91 + ECHEANCE PRET → Remboursement prêt."""
    pass


@pytest.mark.skip(reason="J3")
def test_unknown_returns_none():
    """Type d'opération inconnu doit retourner None (→ délégué au LLM)."""
    pass
