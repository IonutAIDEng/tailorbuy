import pytest

from backend.models import UserPreference
from backend.services.prompt_builder import build_search_prompt, _build_preferences_block


def make_pref(**kwargs):
    defaults = dict(cash_only=False, open_package=False, min_rating=0.0, max_price=None)
    defaults.update(kwargs)
    p = UserPreference()
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


def test_build_prompt_without_preferences_contains_query():
    prompt = build_search_prompt("canapea rosie", None)
    assert "canapea rosie" in prompt


def test_build_prompt_without_preferences_has_no_prefs_block():
    prompt = build_search_prompt("canapea rosie", None)
    assert "<user_preferences>" not in prompt


def test_build_prompt_with_preferences_contains_prefs_block():
    pref = make_pref(cash_only=True)
    prompt = build_search_prompt("canapea rosie", pref)
    assert "<user_preferences>" in prompt
    assert "<cash_on_delivery>true</cash_on_delivery>" in prompt


def test_build_prompt_open_package_included():
    pref = make_pref(open_package=True)
    prompt = build_search_prompt("laptop", pref)
    assert "<open_package>true</open_package>" in prompt


def test_build_prompt_max_price_included_when_set():
    pref = make_pref(max_price=1500)
    prompt = build_search_prompt("telefon", pref)
    assert "<max_price_ron>1500</max_price_ron>" in prompt


def test_build_prompt_max_price_omitted_when_none():
    pref = make_pref(max_price=None)
    prompt = build_search_prompt("telefon", pref)
    assert "<max_price_ron>" not in prompt


def test_build_prompt_min_rating_included():
    pref = make_pref(min_rating=4.5)
    prompt = build_search_prompt("scaun", pref)
    assert "<min_rating>4.5</min_rating>" in prompt


def test_build_prompt_contains_output_schema():
    prompt = build_search_prompt("masa", None)
    assert "products" in prompt
    assert "price_ron" in prompt


def test_build_prompt_instructs_only_available_products():
    prompt = build_search_prompt("frigider", None)
    assert "indisponibil" in prompt or "in stock" in prompt.lower() or "stoc" in prompt


def test_preferences_block_empty_for_none():
    block = _build_preferences_block(None)
    assert block == ""


@pytest.mark.parametrize("cash_only,expected", [(True, "true"), (False, "false")])
def test_preferences_block_cash_on_delivery(cash_only, expected):
    pref = make_pref(cash_only=cash_only)
    block = _build_preferences_block(pref)
    assert f"<cash_on_delivery>{expected}</cash_on_delivery>" in block
