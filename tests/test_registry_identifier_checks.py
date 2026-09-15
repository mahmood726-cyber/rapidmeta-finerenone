import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ssot"))

import registry_identifier_checks as ric  # noqa: E402


def test_404_banner_uses_strong_unsupported_wording():
    store = {
        "pages": {
            "example.html": {
                "identifiers": [
                    {
                        "nct": "NCT05000550",
                        "lane_z_current": {
                            "checked_utc": "2026-09-14T23:59:01Z",
                            "http_status": 404,
                            "pubmed_hits": 0,
                            "europepmc_hits": 0,
                        },
                    }
                ]
            }
        }
    }

    banner = ric.render_banner("example.html", store)

    assert "Registry identifiers NOT FOUND" in banner
    assert "these identifiers do not exist in the registry of record" in banner
    assert "UNSUPPORTED" in banner
    assert "may be real" not in banner
    assert "could not be verified" not in banner
    assert "UNVERIFIED registry ID" not in banner


def test_unmeasured_banner_says_not_checked_not_absent():
    store = {
        "pages": {
            "example.html": {
                "identifiers": [{"nct": "NCT00000000"}],
            }
        }
    }

    banner = ric.render_banner("example.html", store)

    assert "Registry identifiers NOT CHECKED" in banner
    assert "not observed, never absent" in banner


def test_inject_replaces_weak_banner_only():
    store = {
        "pages": {
            "example.html": {
                "identifiers": [
                    {
                        "nct": "NCT05000550",
                        "lane_z_current": {
                            "checked_utc": "2026-09-14T23:59:01Z",
                            "http_status": 404,
                            "pubmed_hits": 0,
                            "europepmc_hits": 0,
                        },
                    }
                ]
            }
        }
    }
    old = (
        '<html><body><div id="overmind-provenance-banner">'
        "9 with UNVERIFIED registry ID -- the trial may be real but its identifier "
        "could not be verified"
        "</div><main>keep me</main></body></html>"
    )

    updated = ric.inject(old, "example.html", store)

    assert updated.count('id="overmind-provenance-banner"') == 1
    assert "UNVERIFIED registry ID" not in updated
    assert "keep me" in updated
    assert ric.strip_banner(updated) == "<html><body><main>keep me</main></body></html>"
