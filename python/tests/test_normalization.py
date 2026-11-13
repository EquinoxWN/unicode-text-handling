"""NormalizationTest.txt (Unicode 15.0.0) against unicodedata.normalize."""

import unicodedata

import pytest

from unicode_text_handling import vectors
from unicode_text_handling.conformance import FORMS, Form, normalization_failures

CASES = vectors.normalization()
SWAPPED: dict[Form, Form] = {"NFC": "NFD", "NFD": "NFC", "NFKC": "NFKD", "NFKD": "NFKC"}


@pytest.mark.parametrize("form", FORMS)
def test_unicodedata_passes_every_case(form: Form) -> None:
    deviations = vectors.expected_deviations(
        "python", "normalization", f"unicodedata.normalize {form}", unicodedata.unidata_version
    )
    assert normalization_failures(CASES, form) == sorted(int(d) for d in deviations)


@pytest.mark.parametrize("form", FORMS)
def test_harness_catches_a_normalizer_that_does_nothing(form: Form) -> None:
    failures = normalization_failures(CASES, form, lambda _f, s: s)
    assert len(failures) > 1000


@pytest.mark.parametrize("form", FORMS)
def test_harness_catches_composed_and_decomposed_swapped(form: Form) -> None:
    def wrong(f: Form, s: str) -> str:
        return unicodedata.normalize(SWAPPED[f], s)

    assert normalization_failures(CASES, form, wrong)


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("column", range(5))
def test_every_column_is_checked(form: Form, column: int) -> None:
    # A normalizer that is wrong only on one column (where that string occurs once) must fail.
    case = next(c for c in CASES if c.columns.count(c.columns[column]) == 1)
    bad = case.columns[column]

    def wrong_on_one(f: Form, s: str) -> str:
        return "�" if s == bad else unicodedata.normalize(f, s)

    assert normalization_failures([case], form, wrong_on_one) == [case.line]
