from scripts.compare_registered_interventions import compare_trial


def test_missing_nct_is_unknown_not_wrong():
    row = compare_trial(
        app="APP.html",
        nct="NCT00000001",
        claimed_name="COAPT",
        registry={},
    )

    assert row["state"] == "NCT_NOT_IN_CACHE"


def test_missing_registry_acronym_is_unverifiable():
    row = compare_trial(
        app="APP.html",
        nct="NCT00000001",
        claimed_name="COAPT",
        registry={
            "NCT00000001": {
                "acronym": None,
                "brief_title": "A Study of Something Else",
                "lead_sponsor": "Example Sponsor",
            }
        },
    )

    assert row["state"] == "UNVERIFIABLE"


def test_roman_numeral_variant_agrees_and_enrollment_is_ignored():
    row = compare_trial(
        app="APP.html",
        nct="NCT00000001",
        claimed_name="ASPIRE-1",
        registry={
            "NCT00000001": {
                "acronym": "Aspire I",
                "brief_title": "A Study of Example Treatment",
                "lead_sponsor": "Example Sponsor",
                "enrollment_count": 776,
            }
        },
    )

    assert row["state"] == "AGREES"


def test_short_registry_acronym_boundary_agrees():
    row = compare_trial(
        app="APP.html",
        nct="NCT00000001",
        claimed_name="EAST-AFNET 4",
        registry={
            "NCT00000001": {
                "acronym": "EAST",
                "brief_title": "Early Treatment of Atrial Fibrillation for Stroke Prevention Trial",
                "lead_sponsor": "Example Sponsor",
            }
        },
    )

    assert row["state"] == "AGREES"


def test_clear_acronym_swap_disagrees():
    row = compare_trial(
        app="APP.html",
        nct="NCT00000001",
        claimed_name="EMERGE",
        registry={
            "NCT00000001": {
                "acronym": "ENGAGE",
                "brief_title": "Phase 3 Study in Early Alzheimer's Disease",
                "lead_sponsor": "Example Sponsor",
            }
        },
    )

    assert row["state"] == "DISAGREES"
