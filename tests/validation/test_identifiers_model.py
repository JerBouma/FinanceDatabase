"""Identifiers Model Tests"""

import pytest

from scripts.validation.identifiers_model import (
    get_cusip_from_authoritative_isin,
    repair_identifier,
    validate_cusip,
    validate_figi,
    validate_isin,
    validate_isin_cusip_consistency,
)


@pytest.mark.parametrize(
    "isin",
    ["US0378331005", "GB0002634946", "AU0000XVGZA3", "XS0971721963"],
)
def test_validate_isin_accepts_valid_values(isin: str) -> None:
    """Test that valid ISINs are accepted."""
    assert validate_isin(isin) is None


@pytest.mark.parametrize(
    "isin",
    [
        "us0378331005",
        " US0378331005 ",
        "US037833100",
        "US037833100A",
    ],
)
def test_validate_isin_rejects_noncanonical_or_invalid_values(isin: str) -> None:
    """Test that non-canonical or invalid ISINs are rejected."""
    assert validate_isin(isin) is not None


def test_validate_isin_reports_checksum_mismatch() -> None:
    """Test that an ISIN checksum mismatch is reported."""
    assert validate_isin("US0378331004") == "checksum mismatch"


@pytest.mark.parametrize("cusip", ["037833100", "594918104", "17275R102"])
def test_validate_cusip_accepts_valid_values(cusip: str) -> None:
    """Test that valid CUSIPs are accepted."""
    assert validate_cusip(cusip) is None


@pytest.mark.parametrize(
    "cusip",
    [
        " 037833100 ",
        "194162103.0",
        "03783310A",
    ],
)
def test_validate_cusip_rejects_noncanonical_or_invalid_values(cusip: str) -> None:
    """Test that non-canonical or invalid CUSIPs are rejected."""
    assert validate_cusip(cusip) is not None


def test_validate_cusip_reports_checksum_mismatch() -> None:
    """Test that a CUSIP checksum mismatch is reported."""
    assert validate_cusip("037833101") == "checksum mismatch"


def test_validate_figi_accepts_valid_value() -> None:
    """Test that a valid FIGI is accepted."""
    assert validate_figi("BBG000BLNQ16") is None


@pytest.mark.parametrize(
    "figi",
    [
        " bbg000blnq16 ",
        "BBG000BLNA16",
        "#REF!",
    ],
)
def test_validate_figi_rejects_noncanonical_or_invalid_values(figi: str) -> None:
    """Test that non-canonical or invalid FIGIs are rejected."""
    assert validate_figi(figi) is not None


def test_validate_figi_reports_checksum_mismatch() -> None:
    """Test that a FIGI checksum mismatch is reported."""
    assert validate_figi("BBG000BLNQ15") == "checksum mismatch"


def test_validate_isin_cusip_consistency() -> None:
    """Test that the ISIN and CUSIP are checked for consistency."""
    assert validate_isin_cusip_consistency("US0378331005", "037833100") is None
    assert validate_isin_cusip_consistency("GB0002634946", "594918104") is None
    assert validate_isin_cusip_consistency("US0378331005", "594918104") == (
        "ISIN national identifier does not match CUSIP"
    )


def test_get_cusip_from_authoritative_isin_returns_embedded_value_when_valid() -> None:
    """Test that the CUSIP embedded in a valid ISIN is returned."""
    assert get_cusip_from_authoritative_isin("US0378331005") == "037833100"


def test_get_cusip_from_authoritative_isin_rejects_invalid_embedded_cusip() -> None:
    """Test that an invalid CUSIP embedded in an ISIN is rejected."""
    assert get_cusip_from_authoritative_isin("US1234567890") is None


def test_repair_identifier_requires_deterministic_evidence() -> None:
    """Test that an identifier is only repaired with deterministic evidence."""
    assert repair_identifier("isin", " us0378331005 ", {}) == "US0378331005"
    assert repair_identifier("figi", " bbg000blnq16 ", {}) == "BBG000BLNQ16"
    assert repair_identifier("isin", "US0378331005.0", {}) == "US0378331005"
    assert repair_identifier("figi", "BBG000BLNQ16.0", {}) == "BBG000BLNQ16"
    assert repair_identifier("cusip", "962166104.0", {}) == "962166104"
    assert (
        repair_identifier("cusip", "4434205.0", {"isin": "US0044342055"}) == "004434205"
    )
    assert repair_identifier("cusip", "2824100", {"isin": "IT0005445280"}) is None
