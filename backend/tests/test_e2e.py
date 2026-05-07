"""Tests end-to-end sur le golden test ECO Steering (J4/J5)."""
import pytest


@pytest.mark.skip(reason="J4")
def test_altran_full_flow():
    """Virement Altran 53 346 € : classé, rapproché, écrit dans la matrice."""
    pass


@pytest.mark.skip(reason="J4")
def test_sekisui_report():
    """Cas FC1140 SEKISUI : échéance décalée proposée automatiquement."""
    pass


@pytest.mark.skip(reason="J4")
def test_sumif_preserved():
    """Après écriture, les formules SUMIF du Budget de tréso sont intactes."""
    pass


@pytest.mark.skip(reason="J5")
def test_golden_comparison():
    """Sortie POC == matrice golden du 16/04 sur les métriques cibles."""
    pass
