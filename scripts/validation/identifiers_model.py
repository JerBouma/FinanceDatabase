"""Identifiers Model"""

__docformat__ = "google"

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from stdnum import cusip, figi, isin
from stdnum.exceptions import InvalidChecksum, ValidationError

FIGI_FIELDS = ("figi", "composite_figi", "shareclass_figi")


@dataclass(frozen=True)
class IdentifierIssue:
    """
    An invalid or inconsistent identifier found in a source CSV row.
    """

    path: Path
    line_number: int
    symbol: str
    field: str
    value: str
    reason: str
    actionable: bool
    replacement: str | None = None


@dataclass(frozen=True)
class AuditResult:
    """
    Summary of an identifier audit.
    """

    issues: tuple[IdentifierIssue, ...]
    files_scanned: int
    identifiers_checked: int
    relationships_checked: int


@dataclass(frozen=True)
class CleanupResult:
    """
    Counts of deterministic repairs and removals applied to one CSV file.
    """

    repaired: int = 0
    cleared: int = 0

    def count_changes(self) -> int:
        """
        Count the changed identifier cells.

        Returns:
            int: The repaired plus the cleared cells.
        """
        return self.repaired + self.cleared


def _validate_standard_number(
    value: str, validator: Callable[[str], str], format_error: str
) -> str | None:
    """
    Run a python-stdnum validator and require canonical stored formatting.
    """
    try:
        canonical = validator(value)
    except InvalidChecksum:
        return "checksum mismatch"
    except ValidationError:
        return format_error
    if canonical != value:
        return format_error
    return None


def validate_isin(value: str) -> str | None:
    """
    Return an ISO 6166 validation error, or ``None`` when valid.
    """
    return _validate_standard_number(
        value,
        isin.validate,
        "expected a canonical 12-character ISIN with a numeric check digit",
    )


def validate_cusip(value: str) -> str | None:
    """
    Return a CUSIP validation error, or ``None`` when valid.
    """
    return _validate_standard_number(
        value,
        cusip.validate,
        "expected a canonical 9-character CUSIP with a check digit",
    )


def validate_figi(value: str) -> str | None:
    """
    Return a FIGI validation error, or ``None`` when valid.
    """
    return _validate_standard_number(
        value,
        figi.validate,
        "expected a canonical 12-character FIGI with a valid prefix",
    )


def validate_isin_cusip_consistency(isin: str, cusip: str) -> str | None:
    """
    Check whether a valid US/Canadian ISIN embeds the supplied CUSIP.
    """
    if not isin or not cusip or isin[:2] not in {"US", "CA"}:
        return None
    if validate_isin(isin) is not None or validate_cusip(cusip) is not None:
        return None
    if isin[2:11] != cusip:
        return "ISIN national identifier does not match CUSIP"
    return None


def get_cusip_from_authoritative_isin(isin_value: str) -> str | None:
    """
    Return the CUSIP embedded in a valid US/Canadian ISIN, the authoritative source.
    """
    embedded_cusip = isin_value[2:11]
    if validate_cusip(embedded_cusip) is not None:
        return None
    return embedded_cusip


def check_isin_precludes_cusip(isin_value: str) -> bool:
    """
    Return True when a valid ISIN's country cannot carry a real CUSIP.

    A CUSIP only exists for US and Canadian securities, so any populated CUSIP
    cell next to a valid non-US/Canadian ISIN is definitely wrong data, not an
    ambiguous one requiring manual review.
    """
    return validate_isin(isin_value) is None and isin_value[:2] not in {"US", "CA"}


STANDARD_VALIDATORS: dict[str, Callable[[str], str]] = {
    "isin": isin.validate,
    "cusip": cusip.validate,
    **{field: figi.validate for field in FIGI_FIELDS},
}

FIELD_VALIDATORS: dict[str, Callable[[str], str | None]] = {
    "isin": validate_isin,
    "cusip": validate_cusip,
    **{field: validate_figi for field in FIGI_FIELDS},
}


def _get_canonical_value(field: str, value: str) -> str | None:
    """
    Return python-stdnum's canonical value when the identifier is valid.
    """
    try:
        return STANDARD_VALIDATORS[field](value)
    except ValidationError:
        return None


def _repair_cusip_from_isin(cusip_value: str, isin_value: str) -> str | None:
    """
    Recover spreadsheet-damaged CUSIPs corroborated by a valid ISIN.
    """
    canonical_isin = _get_canonical_value("isin", isin_value)
    if canonical_isin is None or canonical_isin[:2] not in {"US", "CA"}:
        return None

    embedded_cusip = canonical_isin[2:11]
    if validate_cusip(embedded_cusip) is not None:
        return None

    numeric_value = cusip_value.removesuffix(".0")
    if numeric_value.isdigit() and numeric_value.lstrip("0") == embedded_cusip.lstrip(
        "0"
    ):
        return embedded_cusip
    return None


def repair_identifier(field: str, value: str, row_values: dict[str, str]) -> str | None:
    """
    Return a deterministic replacement for an invalid stored identifier.
    """
    canonical = _get_canonical_value(field, value)
    if canonical is not None and canonical != value:
        return canonical
    without_decimal_suffix = value.removesuffix(".0")
    if without_decimal_suffix != value:
        canonical = _get_canonical_value(field, without_decimal_suffix)
        if canonical == without_decimal_suffix:
            return canonical
    if field == "cusip":
        return _repair_cusip_from_isin(value, row_values.get("isin", ""))
    return None
