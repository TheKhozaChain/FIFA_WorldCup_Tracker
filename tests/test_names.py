"""Team-name normalisation so live providers line up with ratings/baseline."""
from wctracker.baseline import load_baseline
from wctracker.names import CANONICAL, canonical


def test_known_provider_variants_map_to_canonical():
    cases = {
        "Czechia": "Czech Republic",
        "Korea Republic": "South Korea",
        "Türkiye": "Turkey",
        "Côte d'Ivoire": "Ivory Coast",
        "Curaçao": "Curacao",
        "Cabo Verde": "Cape Verde",
        "United States": "USA",
        "IR Iran": "Iran",
        "Congo DR": "DR Congo",
    }
    for provider_name, expected in cases.items():
        assert canonical(provider_name) == expected


def test_canonical_names_are_stable():
    # A name already canonical must pass through unchanged.
    for name in CANONICAL:
        assert canonical(name) == name


def test_accent_and_case_insensitive():
    assert canonical("CURACAO") == "Curacao"
    assert canonical("curaçao") == "Curacao"


def test_unknown_name_passes_through():
    assert canonical("Atlantis") == "Atlantis"


def test_every_canonical_name_has_a_baseline_entry():
    # Guards against the canonical set drifting from the committed baseline.
    baseline = load_baseline()
    if baseline:  # baseline.json is committed, so this normally runs
        missing = CANONICAL - set(baseline)
        assert not missing, f"canonical names missing from baseline: {missing}"
