import re
from pathlib import Path


ROOT = Path('.')
HTML_PATH = ROOT / 'src' / 'agentic_ai_security_lab' / 'console_assets' / 'index.html'
JS_PATH = ROOT / 'src' / 'agentic_ai_security_lab' / 'console_assets' / 'app.js'
SERVER_PATH = ROOT / 'src' / 'agentic_ai_security_lab' / 'console_server.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_no_malformed_selector_helpers_can_abort_console_boot() -> None:
    js = _read(JS_PATH)
    assert 'const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));' in js
    assert re.search(r'\${3,}\(', js) is None
    assert re.search(r'(?<!\$)\$\([^\n;]*\)\.forEach', js) is None


def test_every_static_view_and_jump_target_exists() -> None:
    html = _read(HTML_PATH)
    views = set(re.findall(r'<section\s+id="view-([^"]+)"', html))
    data_views = set(re.findall(r'data-view="([^"]+)"', html))
    data_jumps = set(re.findall(r'data-jump="([^"]+)"', html))
    assert data_views <= views
    assert data_jumps <= views


def test_every_static_scroll_target_exists() -> None:
    html = _read(HTML_PATH)
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    scroll_targets = set(re.findall(r'data-scroll-target="([^"]+)"', html))
    assert scroll_targets <= ids


def test_ui_api_routes_exist_on_server() -> None:
    js = _read(JS_PATH)
    server = _read(SERVER_PATH)
    direct_api_routes = set(re.findall(r'api\("([^"]+)"', js))
    indirect_action_routes = set(re.findall(r'(?:targetAction|vmAction)\("([^"]+)"', js))
    ui_routes = direct_api_routes | indirect_action_routes
    server_routes = set(re.findall(r'path\s*==\s*"([^"]+)"', server))
    assert ui_routes <= server_routes


def test_expected_static_control_handlers_are_wired() -> None:
    html = _read(HTML_PATH)
    js = _read(JS_PATH)
    expected_ids = {
        'command-button', 'pricing-button', 'run-pack', 'open-runner',
        'quick-run', 'generate-interview', 'load-simulation', 'register-target',
        'close-runner', 'drawer-run', 'close-detail',
    }
    html_ids = set(re.findall(r'<button[^>]*\sid="([^"]+)"', html))
    assert expected_ids <= html_ids
    for button_id in expected_ids:
        assert f'$("#{button_id}").addEventListener' in js


def test_expected_dynamic_actions_have_handler_contracts() -> None:
    js = _read(JS_PATH)
    expected = {
        'run-hunt': '$$(".run-hunt").forEach',
        'open-lab': '$$(".open-lab").forEach',
        'open-runner-lab': '$$(".open-runner-lab").forEach',
        'run-secure': '$$(".run-secure").forEach',
        'view-finding': '$$(".view-finding").forEach',
        'create-case': '$$(".create-case").forEach',
        'evaluate-interview': '$$(".evaluate-interview").forEach',
        'speak-question': '$$(".speak-question").forEach',
        'dictate-answer': '$$(".dictate-answer").forEach',
        'reveal-hint': '$$(".reveal-hint").forEach',
        'evaluate-simulation': '$$(".evaluate-simulation").forEach',
        'dictate-simulation': '$$(".dictate-simulation").forEach',
        'vm-start': '$$(".vm-start").forEach',
        'vm-reset': '$$(".vm-reset").forEach',
        'vm-stop': '$$(".vm-stop").forEach',
        'target-analyze': '$$(".target-analyze").forEach',
        'target-clone': '$$(".target-clone").forEach',
        'target-scaffold': '$$(".target-scaffold").forEach',
        'target-run': '$$(".target-run").forEach',
        'pricing-cta': '$$(".pricing-cta").forEach',
    }
    for css_class, handler_token in expected.items():
        assert css_class in js
        assert handler_token in js
    assert 'root.querySelector(".apply-improved")' in js
    assert 'const create=$(".detail-create-case")' in js


def test_roadmap_features_are_not_presented_as_live() -> None:
    product = _read(ROOT / 'src' / 'agentic_ai_security_lab' / 'product_experiences.py')
    html = _read(HTML_PATH)
    assert '"billing_live": False' in product
    assert '"status": "hosted-labs-coming-soon"' in product
    assert '"plan_id": "teams"' in product
    assert '"status": "roadmap"' in product
    assert 'Billing and subscription enforcement are not enabled' in html


def test_dependency_gated_features_have_fallbacks() -> None:
    js = _read(JS_PATH)
    vm = _read(ROOT / 'src' / 'agentic_ai_security_lab' / 'vm_runtime.py')
    evaluator = _read(ROOT / 'src' / 'agentic_ai_security_lab' / 'model_evaluator.py')
    assert 'SpeechRecognition' in js
    assert 'speechSynthesis' in js
    assert 'Multipass is not installed' in vm
    assert 'Deterministic local evaluator active' in evaluator