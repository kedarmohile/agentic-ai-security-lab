from pathlib import Path

from scripts.check_links import discover_external_urls, validate_internal_links


def test_all_internal_repository_links_resolve() -> None:
    problems = validate_internal_links()
    assert problems == []


def test_expected_external_destinations_are_discoverable() -> None:
    urls = set(discover_external_urls())

    expected = {
        "https://github.com/NVIDIA/garak/issues/2453",
        "https://github.com/elastic/detection-rules/issues/6722",
        "https://www.hackthebox.com/business/enterprise-platform",
        "https://www.immersivelabs.com/solutions/cyber-resilience-metrics",
        "https://www.immersivelabs.com/platform",
        "https://atlas.mitre.org/",
        "https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center",
        "https://multipass.run/",
        "https://api.openai.com/v1/responses",
    }

    assert expected.issubset(urls)


def test_console_hyperlink_assets_exist() -> None:
    root = Path("src/agentic_ai_security_lab/console_assets")
    for asset in ("shield.svg", "styles.css", "app.js", "index.html"):
        assert (root / asset).is_file()
