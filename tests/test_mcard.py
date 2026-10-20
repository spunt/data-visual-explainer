import copy
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from markupsafe import escape

from mcard.lint import lint
from mcard.model import Card, fmt, window_range
from mcard.render import render_card, render_index

ROOT = Path(__file__).resolve().parent.parent
CARDS = sorted((ROOT / "cards").glob("*.yaml"))


def card_from(raw: dict, tmp_path: Path) -> Card:
    p = tmp_path / "c.yaml"
    p.write_text(yaml.safe_dump(raw, sort_keys=False))
    return Card.load(p)


@pytest.fixture
def did_raw():
    return yaml.safe_load((ROOT / "cards" / "minimum-wage-did.yaml").read_text())


@pytest.mark.parametrize("path", CARDS, ids=lambda p: p.stem)
def test_shipped_cards_have_no_errors(path):
    card = Card.load(path)
    errors = [f for f in lint(card) if f.level == "error"]
    assert not errors, errors


@pytest.mark.parametrize("path", CARDS, ids=lambda p: p.stem)
def test_render_is_self_contained(path, tmp_path):
    card = Card.load(path)
    out = render_card(card, tmp_path)
    html = out["explorer"].read_text()
    # no external resources: scripts, styles, images or fonts fetched over the network
    assert not re.search(r'<(script|link|img)[^>]+(src|href)="https?://', html)
    assert "@import" not in html and "url(http" not in html
    assert card["gist"]["key_caveat"].split()[0] in html
    assert html.count('role="tooltip"') == len(card.get("glossary", []))
    assert out["label"].exists()
    assert out["methods"].read_text().lstrip().startswith(f"# {card['title']}")


def test_index(tmp_path):
    p = render_index([Card.load(c) for c in CARDS], tmp_path)
    assert all(str(escape(Card.load(c)["title"])) in p.read_text() for c in CARDS)


def test_did_recompute_matches_readout(did_raw, tmp_path):
    val, formula = card_from(did_raw, tmp_path).recompute()
    assert val == pytest.approx(2.754, abs=1e-3)
    assert "−" in formula


def test_recompute_mismatch_is_an_error(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    raw["results"]["estimate"]["value"] = 3.9
    raw["gist"]["headline"]["value"] = 3.9
    codes = {f.code for f in lint(card_from(raw, tmp_path)) if f.level == "error"}
    assert "recompute" in codes


def test_broken_references_are_errors(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    raw["grammar"]["measures"][0]["window"] = "nope"
    raw["fine_print"]["caveats"][0]["src"] = "S99"
    codes = {f.code for f in lint(card_from(raw, tmp_path)) if f.level == "error"}
    assert {"ref-window", "ref-source"} <= codes


def test_immature_window_is_an_error(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    raw["results"]["latest_anchor"] = "1992-04-01"
    raw["results"]["data_complete_through"] = "1992-11-30"
    codes = {f.code for f in lint(card_from(raw, tmp_path)) if f.level == "error"}
    assert "maturity" in codes


def test_unglossed_jargon_is_flagged(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    raw["gist"]["key_caveat"] += " The IPTW weights matter."
    msgs = [f.message for f in lint(card_from(raw, tmp_path)) if f.code == "jargon"]
    assert any("IPTW" in m for m in msgs)


def test_did_alias_is_case_sensitive(did_raw, tmp_path):
    card = card_from(did_raw, tmp_path)
    html = render_card(card, tmp_path)["explorer"].read_text()
    assert ">did</button>" not in html


def test_formatting():
    assert fmt(0.427, "pp", signed=True) == "+0.43 pp"
    assert fmt(19.4, "percent") == "19.4%"
    assert fmt(-0.5, "days", signed=True) == "−0.50 days"
    assert window_range({"unit": "day", "start": 1, "end": 29}) == "days 1–28"
    assert window_range({"unit": "day", "start": -28, "end": 0}) == "days −28 to −1"
    assert "not including, 13" in window_range({"unit": "month", "start": 12, "end": 13})


def test_template_is_flagged_unfinished(tmp_path):
    raw = yaml.safe_load((ROOT / "schema" / "card_template.yaml").read_text())
    codes = {f.code for f in lint(card_from(raw, tmp_path)) if f.level == "error"}
    assert "unfinished" in codes


def test_definition_only_card(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    del raw["gist"]["headline"]
    raw["results"] = {"status": "not_run", "sensitivity": [{"label": "planned variant", "value": 0}]}
    card = card_from(raw, tmp_path)
    assert not [f for f in lint(card) if f.level == "error"]
    out = render_card(card, tmp_path)
    assert "Not measured yet" in out["explorer"].read_text()
    assert "Not measured yet" in out["methods"].read_text()
    assert "Not measured yet" in out["label"].read_text()


def test_missing_headline_without_not_run_is_error(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    del raw["gist"]["headline"]
    codes = {f.code for f in lint(card_from(raw, tmp_path)) if f.level == "error"}
    assert "headline" in codes


def test_yaml_error_is_friendly(tmp_path):
    from mcard.cli import main
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: metric-card/1\nglossary:\n  - {term: x, plain: a: b}\n")
    assert main(["lint", str(bad)]) == 2


def test_not_run_with_result_fields_warns(did_raw, tmp_path):
    raw = copy.deepcopy(did_raw)
    del raw["gist"]["headline"]
    raw["results"] = {"status": "not_run", "data_complete_through": "2026-09-07"}
    codes = {f.code for f in lint(card_from(raw, tmp_path))}
    assert "not-run-results" in codes


def test_missing_dependency_gives_install_hint_not_traceback():
    code = "import sys, runpy; sys.modules['jsonschema'] = None; runpy.run_module('mcard', run_name='__main__')"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 1
    assert "pip install pyyaml jinja2 jsonschema" in r.stderr
    assert "Traceback" not in r.stderr


def test_new_hint_names_the_command_that_was_run(tmp_path):
    mcard = ROOT / "bin" / "mcard"
    env = {**os.environ, "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}"}
    r = subprocess.run([str(mcard), "new", "demo", "--dir", str(tmp_path)], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert f"run: {mcard} lint {tmp_path / 'demo.yaml'}" in r.stdout
