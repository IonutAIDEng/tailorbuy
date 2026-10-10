import pytest

from backend.models import UserPreference
from backend.services.prompt_builder import build_search_prompt, _build_preferences_block


def make_pref(**kwargs):
    defaults = dict(cash_only=False, open_package=False, min_rating=0.0, max_price=None,
                    min_review_count=None, new_only=False, search_emag=True, search_altex=True)
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


def test_build_prompt_open_package_adds_deschidere_colet_to_query():
    pref = make_pref(open_package=True)
    prompt = build_search_prompt("laptop", pref)
    assert "deschidere colet" in prompt


def test_build_prompt_open_package_hard_filter_mentions_deschidere_colet():
    pref = make_pref(open_package=True)
    prompt = build_search_prompt("laptop", pref)
    assert "deschidere colet" in prompt
    assert "resigilat" not in prompt.split("<pipeline>")[1].split("STEP 2")[1].split("STEP 3")[0]


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


def test_build_prompt_new_only_included():
    pref = make_pref(new_only=True)
    prompt = build_search_prompt("laptop", pref)
    assert "<new_only>true</new_only>" in prompt


def test_build_prompt_new_only_excludes_search_terms():
    pref = make_pref(new_only=True)
    prompt = build_search_prompt("laptop", pref)
    assert "-resigilat" in prompt
    assert "-reconditionat" in prompt


def test_build_prompt_new_only_false_does_not_add_exclusions():
    pref = make_pref(new_only=False)
    prompt = build_search_prompt("laptop", pref)
    assert "-resigilat" not in prompt


def test_build_prompt_min_review_count_included_when_set():
    pref = make_pref(min_review_count=20)
    prompt = build_search_prompt("telefon", pref)
    assert "<min_review_count>20</min_review_count>" in prompt


def test_build_prompt_min_review_count_omitted_when_none():
    pref = make_pref(min_review_count=None)
    prompt = build_search_prompt("telefon", pref)
    assert "<min_review_count>" not in prompt


def test_build_prompt_min_review_count_hard_filter_included():
    pref = make_pref(min_review_count=15)
    prompt = build_search_prompt("casti", pref)
    assert "review_count < 15" in prompt


def test_build_prompt_emag_only_search():
    pref = make_pref(search_emag=True, search_altex=False)
    prompt = build_search_prompt("laptop", pref)
    assert "site:emag.ro" in prompt
    assert "site:altex.ro" not in prompt


def test_build_prompt_altex_only_search():
    pref = make_pref(search_emag=False, search_altex=True)
    prompt = build_search_prompt("laptop", pref)
    assert "site:altex.ro" in prompt
    assert "site:emag.ro" not in prompt


def test_build_prompt_both_stores_by_default():
    pref = make_pref()
    prompt = build_search_prompt("laptop", pref)
    assert "site:emag.ro" in prompt
    assert "site:altex.ro" in prompt


def test_build_prompt_fallback_to_both_stores_when_none_selected():
    pref = make_pref(search_emag=False, search_altex=False)
    prompt = build_search_prompt("laptop", pref)
    assert "site:emag.ro" in prompt
    assert "site:altex.ro" in prompt


def test_build_prompt_stores_in_preferences_block():
    pref = make_pref(search_emag=True, search_altex=False)
    prompt = build_search_prompt("laptop", pref)
    assert "<search_stores>eMAG</search_stores>" in prompt
