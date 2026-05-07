"""
Drug information module - queries OpenFDA and RxNorm APIs.
No API key required for OpenFDA. RxNorm is free.
"""
import requests
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

OPENFDA_URL = "https://api.fda.gov/drug/label.json"
RXNORM_URL  = "https://rxnav.nlm.nih.gov/REST"


def _get(url, params=None, timeout=5):
    try:
        # verify=False handles self-signed certs on restricted networks
        r = requests.get(url, params=params, timeout=timeout, verify=False)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning(f"API call failed: {e}")
    return None


# ── OpenFDA ──────────────────────────────────────────────────────────────────

def get_fda_info(drug_name: str) -> dict:
    """Return warnings, food interactions, and usage from OpenFDA."""
    data = _get(OPENFDA_URL, params={"search": f"openfda.brand_name:{drug_name}", "limit": 1})
    if not data:
        data = _get(OPENFDA_URL, params={"search": f"openfda.generic_name:{drug_name}", "limit": 1})
    if not data or not data.get("results"):
        return {}

    result = data["results"][0]
    return {
        "warnings":           _first(result, "warnings"),
        "food_interactions":  _first(result, "food_and_drug_interaction"),
        "how_to_use":         _first(result, "dosage_and_administration"),
        "precautions":        _first(result, "precautions"),
        "drug_interactions":  _first(result, "drug_interactions"),
        "indications":        _first(result, "indications_and_usage"),
    }


def _first(d: dict, key: str, max_len=400) -> str:
    val = d.get(key)
    if isinstance(val, list) and val:
        return val[0][:max_len]
    return ""


# ── RxNorm ───────────────────────────────────────────────────────────────────

def get_rxcui(drug_name: str) -> str | None:
    """Get RxNorm concept ID for a drug name."""
    data = _get(f"{RXNORM_URL}/rxcui.json", params={"name": drug_name, "search": 1})
    if data:
        return data.get("idGroup", {}).get("rxnormId", [None])[0]
    return None


def get_drug_interactions(drug_names: list) -> list:
    """
    Check interactions between a list of drugs using RxNorm.
    Returns list of interaction strings.
    """
    rxcuis = []
    for name in drug_names:
        cid = get_rxcui(name)
        if cid:
            rxcuis.append(cid)

    if len(rxcuis) < 2:
        return []

    rxcui_str = "+".join(rxcuis)
    data = _get(f"{RXNORM_URL}/interaction/list.json", params={"rxcuis": rxcui_str})
    if not data:
        return []

    interactions = []
    for group in data.get("fullInteractionTypeGroup", []):
        for itype in group.get("fullInteractionType", []):
            for pair in itype.get("interactionPair", []):
                desc = pair.get("description", "")
                severity = pair.get("severity", "")
                if desc:
                    interactions.append(f"[{severity}] {desc}" if severity else desc)
    return interactions[:5]  # cap at 5


# ── Combined summary ──────────────────────────────────────────────────────────

def get_medicine_summary(drug_name: str) -> dict:
    """Return a combined summary for a single drug."""
    fda = get_fda_info(drug_name)
    return {
        "name":              drug_name,
        "how_to_use":        fda.get("how_to_use", ""),
        "food_interactions": fda.get("food_interactions", ""),
        "warnings":          fda.get("warnings", ""),
        "precautions":       fda.get("precautions", ""),
        "drug_interactions": fda.get("drug_interactions", ""),
        "indications":       fda.get("indications", ""),
    }


def get_prescription_summary(medicines: list) -> dict:
    """
    Given a list of {name, dosage} dicts, return:
    - per-medicine summaries
    - cross-drug interaction warnings
    """
    summaries = []
    names = [m.get("name", "") for m in medicines if m.get("name")]

    for name in names:
        s = get_medicine_summary(name)
        summaries.append(s)

    interactions = get_drug_interactions(names)

    return {
        "medicines":     summaries,
        "interactions":  interactions,
    }
