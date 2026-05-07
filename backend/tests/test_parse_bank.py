"""Tests Agent Lecteur — parsing CSV bancaire (J2)."""
import pytest


@pytest.mark.skip(reason="J2")
def test_csv_encoding():
    """Le CSV doit être lu en Windows-1252 sans UnicodeDecodeError."""
    pass


@pytest.mark.skip(reason="J2")
def test_csv_header_line7():
    """L'en-tête doit être capturé à la ligne 7 (index 6)."""
    pass


@pytest.mark.skip(reason="J2")
def test_type_operation_parsed():
    """La colonne Type d'opération doit contenir les codes codifiés (44, 06, 08…)."""
    pass


@pytest.mark.skip(reason="J2")
def test_55_transactions():
    """Le CSV de mars doit produire exactement 55 transactions."""
    pass
