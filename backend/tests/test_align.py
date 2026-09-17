"""Tests for stereo-aware Needleman-Wunsch alignment."""

import pytest

from peptorama.processing.align import (
    make_match_fn,
    make_score_fn,
    needleman_wunsch,
    stereo_eq,
)


def seq(*residues):
    """Build a sequence of (residue, stereo) tuples, defaulting stereo to 'L'.

    seq("A", "G") -> [("A", "L"), ("G", "L")]
    seq(("A", "D")) -> [("A", "D")]
    """
    return [r if isinstance(r, tuple) else (r, "L") for r in residues]


# Check stereochemisty matching is correct
@pytest.mark.parametrize(
    "a, b, mode, expected",
    [
        # relaxed: stereo never matters
        ("L", "D", "relaxed", True),
        ("L", "flat", "relaxed", True),
        ("L", "L", "relaxed", True),
        # strict: exact equality only
        ("L", "L", "strict", True),
        ("L", "D", "strict", False),
        ("flat", "L", "strict", False),
        ("flat", "flat", "strict", True),
        # moderate: flat matches anything, otherwise exact
        ("L", "L", "moderate", True),
        ("L", "D", "moderate", False),
        ("flat", "D", "moderate", True),
        ("L", "flat", "moderate", True),
        ("flat", "flat", "moderate", True),
    ],
)
def test_stereo_eq(a, b, mode, expected):
    assert stereo_eq(a, b, mode) is expected


@pytest.mark.parametrize("mode", ["relaxed", "strict", "moderate"])
def test_stereo_eq_is_symmetric(mode):
    values = ["L", "D", "flat"]
    for a in values:
        for b in values:
            assert stereo_eq(a, b, mode) == stereo_eq(b, a, mode)


# Test the make_match_fn
@pytest.mark.parametrize("mode", ["relaxed", "strict", "moderate"])
def test_match_requires_same_residue_in_every_mode(mode):
    match = make_match_fn(mode)
    assert match(("A", "L"), ("G", "L")) is False
    assert match(("A", "flat"), ("G", "flat")) is False


@pytest.mark.parametrize(
    "a, b, mode, expected",
    [
        (("A", "L"), ("A", "L"), "strict", True),
        (("A", "L"), ("A", "D"), "strict", False),
        (("A", "L"), ("A", "D"), "moderate", False),
        (("A", "flat"), ("A", "D"), "moderate", True),
        (("A", "L"), ("A", "D"), "relaxed", True),
    ],
)
def test_match_uses_stereo_mode(a, b, mode, expected):
    assert make_match_fn(mode)(a, b) is expected


# Test scoring function
def test_score_fn_default_scores():
    score = make_score_fn("strict")
    assert score(("A", "L"), ("A", "L")) == 1
    assert score(("A", "L"), ("A", "D")) == -1
    assert score(("A", "L"), ("G", "L")) == -1


def test_score_fn_custom_scores():
    score = make_score_fn("moderate", match_score=5, mismatch_score=-3)
    assert score(("A", "flat"), ("A", "D")) == 5
    assert score(("A", "L"), ("A", "D")) == -3


# Test alignment


@pytest.fixture
def strict_score():
    return make_score_fn("strict")


def test_identical_sequences(strict_score):
    s = seq("A", ("G", "flat"), "K")
    assert needleman_wunsch(s, s, strict_score) == "==="


def test_single_mismatch(strict_score):
    assert needleman_wunsch(seq("A"), seq("G"), strict_score) == "≠"


def test_all_mismatches_prefer_diagonal(strict_score):
    # Diagonal (-2) ties with a gap path; ties resolve to the diagonal.
    assert needleman_wunsch(seq("A", "A"), seq("G", "G"), strict_score) == "≠≠"


def test_gap_in_second_sequence(strict_score):
    assert needleman_wunsch(seq("A", "G", "C"), seq("A", "C"), strict_score) == "=1="


def test_gap_in_first_sequence(strict_score):
    assert needleman_wunsch(seq("A", "C"), seq("A", "G", "C"), strict_score) == "=2="


def test_zero_gap_penalty_prefers_gaps_over_mismatch(strict_score):
    assert needleman_wunsch(seq("A"), seq("G"), strict_score, gap=0) == "21"


@pytest.mark.parametrize(
    "mode, expected",
    [("strict", "≠"), ("moderate", "≠"), ("relaxed", "=")],
)
def test_alignment_respects_stereo_mode_l_vs_d(mode, expected):
    result = needleman_wunsch(seq(("A", "L")), seq(("A", "D")), make_score_fn(mode))
    assert result == expected


@pytest.mark.parametrize(
    "mode, expected",
    [("strict", "≠"), ("moderate", "="), ("relaxed", "=")],
)
def test_alignment_respects_stereo_mode_flat(mode, expected):
    result = needleman_wunsch(seq(("A", "flat")), seq(("A", "D")), make_score_fn(mode))
    assert result == expected
