import json
import re
import threading
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

from agentic_ai_security_lab.console_server import create_server


def _start_server(tmp_path: Path):
    server = create_server("127.0.0.1", 0, tmp_path / "state")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def _stop_server(server, thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_paid_acceptance_clicks_primary_product_surface(tmp_path: Path) -> None:
    target_repo = tmp_path / "target-repo"
    target_repo.mkdir()
    (target_repo / "agent.py").write_text(
        "def browser_tool():\n    return 'synthetic'\n",
        encoding="utf-8",
    )

    server, thread, base = _start_server(tmp_path)
    page_errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("dialog", lambda dialog: dialog.accept("secure") if dialog.type == "prompt" else dialog.accept())

            page.goto(base, wait_until="networkidle")
            page.wait_for_selector("#academy-paths .mission-row")
            assert page_errors == []

            # Every sidebar destination must become the active view.
            for view in (
                "start",
                "pricing",
                "command",
                "hunts",
                "findings",
                "runs",
                "cases",
                "labs",
                "graph",
                "evidence",
            ):
                page.locator(f'.nav-item[data-view="{view}"]').click()
                expect(page.locator(f"#view-{view}")).to_have_class(re.compile(r".*\bactive\b.*"))

            # Top-bar pricing and product tabs.
            page.locator("#pricing-button").click()
            expect(page.locator("#view-pricing")).to_have_class(re.compile(r".*\bactive\b.*"))
            for product in ("start", "career", "target"):
                page.locator(f'.product-tab[data-product-view="{product}"]').click()
                expect(page.locator(f"#view-{product}")).to_have_class(re.compile(r".*\bactive\b.*"))

            # Command palette opens and a navigation item closes it again.
            page.locator("#command-button").click()
            expect(page.locator("#command-palette")).to_have_class(re.compile(r".*\bopen\b.*"))
            page.locator(".palette-item").first.click()
            expect(page.locator("#command-palette")).not_to_have_class(re.compile(r".*\bopen\b.*"))

            # Run-lab drawer opens/closes.
            page.locator("#open-runner").click()
            expect(page.locator("#run-drawer")).to_have_class(re.compile(r".*\bopen\b.*"))
            page.locator("#close-runner").click()
            expect(page.locator("#run-drawer")).not_to_have_class(re.compile(r".*\bopen\b.*"))

            # Quick deterministic run produces a run detail.
            page.locator('.nav-item[data-view="command"]').click()
            page.locator("#quick-lab").select_option("lab01")
            page.locator("#quick-mode").select_option("secure")
            page.locator("#quick-run").click()
            page.wait_for_selector("#detail-drawer.open")
            expect(page.locator("#detail-title")).to_contain_text("Memory")
            page.locator("#close-detail").click()

            # Runs + Evidence become populated and interactive.
            page.locator('.nav-item[data-view="runs"]').click()
            page.wait_for_selector(".run-table-row")
            page.locator(".run-table-row").first.click()
            page.wait_for_selector("#detail-drawer.open")
            page.locator("#close-detail").click()

            page.locator('.nav-item[data-view="evidence"]').click()
            page.wait_for_selector("[data-evidence-run]")
            page.locator("[data-evidence-run]").first.click()

            # Labs dynamic actions.
            page.locator('.nav-item[data-view="labs"]').click()
            page.locator(".open-runner-lab").first.click()
            page.wait_for_selector("#run-drawer.open")
            page.locator("#close-runner").click()
            page.locator(".run-secure").first.click()
            page.wait_for_selector("#detail-drawer.open")
            page.locator("#close-detail").click()

            # Hunts dynamic actions.
            page.locator('.nav-item[data-view="hunts"]').click()
            page.locator(".open-lab").first.click()
            page.wait_for_selector("#run-drawer.open")
            page.locator("#close-runner").click()
            page.locator(".run-hunt").first.click()
            page.wait_for_selector("#detail-drawer.open")
            page.locator("#close-detail").click()

            # Run Hunt Pack accepts the confirmation and creates findings.
            page.locator("#run-pack").click()
            page.wait_for_selector("#view-findings.active")
            page.wait_for_selector(".finding-card")

            # Finding evidence + case creation.
            page.locator(".view-finding").first.click()
            page.wait_for_selector("#detail-drawer.open")
            page.locator("#close-detail").click()
            page.locator(".create-case").first.click()
            page.wait_for_selector("#view-cases.active")
            page.wait_for_selector(".case-card")

            # Pricing page monthly/annual + all plan CTAs.
            page.locator("#pricing-button").click()
            page.locator('.billing-option[data-billing="annual"]').click()
            expect(page.locator('.billing-option[data-billing="annual"]')).to_have_class(re.compile(r".*\bactive\b.*"))

            page.locator('.pricing-cta[data-plan="free"]').click()
            expect(page.locator("#view-start")).to_have_class(re.compile(r".*\bactive\b.*"))

            page.locator("#pricing-button").click()
            page.locator('.pricing-cta[data-plan="core"]').click()
            expect(page.locator("#view-career")).to_have_class(re.compile(r".*\bactive\b.*"))
            expect(page.locator("#career-simulation-panel")).to_have_class(re.compile(r".*\bactive\b.*"))

            page.locator("#pricing-button").click()
            page.locator('.pricing-cta[data-plan="pro"]').click()
            expect(page.locator("#view-career")).to_have_class(re.compile(r".*\bactive\b.*"))

            page.locator("#pricing-button").click()
            page.locator('.pricing-cta[data-plan="teams"]').click()
            expect(page.locator("#view-target")).to_have_class(re.compile(r".*\bactive\b.*"))

            # Career Interview Studio: level switching, generation, evaluation.
            page.locator('.product-tab[data-product-view="career"]').click()
            page.locator('.career-mode-tab[data-career-mode="interview"]').click()
            page.locator("#career-role").select_option("ai-security")
            page.locator("#career-level").select_option("principal")
            page.locator("#generate-interview").click()
            page.wait_for_selector(".interactive-question")
            expect(page.locator(".interview-head")).to_contain_text("PRINCIPAL")

            answer = (
                "I would define trust boundaries, use workload identity and exact "
                "authorization for privileged tools, preserve telemetry, measure "
                "coverage and failure rates, and define exception handling at enterprise scale."
            )
            page.locator(".interview-answer").first.fill(answer)
            page.locator(".evaluate-interview").first.click()
            page.wait_for_selector(".evaluation-result.visible")
            expect(page.locator(".evaluation-result.visible").first).to_contain_text(
                "BEST SAMPLE ANSWER"
            )

            # Voice controls must be clickable even if speech recognition is unsupported.
            page.locator(".speak-question").first.click()
            page.locator(".dictate-answer").first.click()

            # Career Simulation Range: load, search, hint, validate.
            page.locator('.career-mode-tab[data-career-mode="simulation"]').click()
            page.wait_for_selector("#career-simulation-panel.active")
            page.locator("#load-simulation").click()
            page.wait_for_selector(".simulation-task")
            page.locator("#simulation-search").fill("approval")
            page.locator("#run-simulation-search").click()
            page.locator(".reveal-hint").first.click()
            page.wait_for_selector(".hint-item")
            page.locator(".simulation-answer").first.fill(
                "The control must distinguish trusted approval from untrusted context, "
                "correlate the request, block unauthorized execution, and preserve evidence."
            )
            page.locator(".evaluate-simulation").first.click()
            page.wait_for_selector(".simulation-task .evaluation-result.visible")

            # VM is dependency-gated. If Multipass is absent, clicking Start VM must
            # produce a visible error instead of silently failing.
            with urllib.request.urlopen(base + "/api/vm/catalog") as response:
                vm_catalog = json.loads(response.read().decode("utf-8"))
            if not vm_catalog["host"]["available"] and page.locator(".vm-start").count():
                page.locator(".vm-start").first.click()
                page.wait_for_selector(".toast.error")
                expect(page.locator(".toast.error").last).to_contain_text("Multipass")

            # Target Lab local registration/analyze/scaffold.
            page.locator('.product-tab[data-product-view="target"]').click()
            page.locator("#target-name").fill("e2e-target")
            page.locator("#target-source").select_option("local")
            page.locator("#target-location").fill(str(target_repo))
            page.locator("#register-target").click()
            page.wait_for_selector(".target-item")
            page.locator(".target-item").first.click()

            if page.locator(".target-analyze").count():
                page.locator(".target-analyze").first.click()
            page.wait_for_timeout(150)

            if page.locator(".target-scaffold").count():
                page.locator(".target-scaffold").first.click()
                page.wait_for_timeout(150)
                assert (target_repo / ".aasl" / "target.json").is_file()

            # Target test without a configured adapter should fail visibly, not be dead.
            if page.locator(".target-run").count():
                page.locator(".target-run").first.click()
                page.wait_for_selector(".toast.error")
                expect(page.locator(".toast.error").last).to_contain_text("manifest")

            assert page_errors == []
            browser.close()
    finally:
        _stop_server(server, thread)
