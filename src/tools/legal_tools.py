import json
from pathlib import Path

from langchain_core.tools import tool

_DATA = Path(__file__).parent.parent.parent / "data"


def _regs() -> dict:
    with open(_DATA / "regulations.json", encoding="utf-8") as f:
        return json.load(f)


@tool
def validate_incoterm(incoterm: str) -> str:
    """Verify that an Incoterm is valid under Incoterms® 2020."""
    regs = _regs()
    valid = regs["incoterms_2020"]
    is_valid = incoterm.upper() in valid
    return json.dumps(
        {
            "incoterm": incoterm.upper(),
            "valid": is_valid,
            "valid_incoterms_2020": valid,
            "note": "Incoterms® 2020 published by ICC." if is_valid else "Invalid — use one of the listed terms.",
        }
    )


@tool
def check_applicable_tariffs(origin_country: str, destination_country: str, material: str) -> str:
    """
    Return applicable import tariffs for a material shipped between two countries.
    Use ISO country codes (e.g. 'DE', 'ES') or region names ('EU').
    """
    regs = _regs()
    eu_countries = {
        "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
        "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
        "NL", "PL", "PT", "RO", "SE", "SI", "SK",
    }
    origin_eu = origin_country.upper() in eu_countries or origin_country.upper() == "EU"
    dest_eu = destination_country.upper() in eu_countries or destination_country.upper() == "EU"

    if origin_eu and dest_eu:
        tariff_data = regs["tariffs"]["EU_to_EU"].get(
            material, {"rate_pct": 0.0, "note": "EU single market - no tariffs"}
        )
        category = "EU_to_EU"
    else:
        tariff_data = regs["tariffs"]["non_EU_to_EU"].get(
            material, {"rate_pct": 5.0, "note": "Standard EU MFN tariff applies"}
        )
        category = "non_EU_to_EU"

    return json.dumps(
        {
            "origin": origin_country,
            "destination": destination_country,
            "material": material,
            "tariff_category": category,
            "tariff_details": tariff_data,
        }
    )


@tool
def check_carbon_compliance(material: str, carbon_per_unit_kg: float, quantity: float) -> str:
    """
    Verify whether the material's carbon footprint meets EU CBAM thresholds.
    Returns compliance status and total carbon impact.
    """
    regs = _regs()
    limits = regs["carbon_limits_kg_co2_per_ton"]
    limit = limits.get(material)

    if limit is None:
        return json.dumps({"error": f"No carbon limit defined for '{material}'.", "available": list(limits.keys())})

    compliant = carbon_per_unit_kg <= limit
    total_co2 = round(carbon_per_unit_kg * quantity, 2)

    return json.dumps(
        {
            "material": material,
            "carbon_per_unit_kg": carbon_per_unit_kg,
            "eu_cbam_limit_kg": limit,
            "compliant": compliant,
            "total_co2_kg": total_co2,
            "note": regs["carbon_limits_kg_co2_per_ton"].get("note", ""),
        }
    )


@tool
def validate_payment_terms(payment_terms: str) -> str:
    """
    Validate payment terms against EU Late Payment Directive and allowed terms list.
    """
    regs = _regs()
    pt_config = regs["payment_terms"]
    allowed = pt_config["allowed"]
    max_days = pt_config["max_days"]

    is_allowed = payment_terms.upper() in [t.upper() for t in allowed]

    # Extract days from NET_NN pattern
    import re
    m = re.search(r"NET[_\s]?(\d+)", payment_terms.upper())
    days = int(m.group(1)) if m else None
    exceeds_limit = days is not None and days > max_days

    return json.dumps(
        {
            "payment_terms": payment_terms,
            "recognized": is_allowed,
            "days_extracted": days,
            "exceeds_max_days": exceeds_limit,
            "max_allowed_days": max_days,
            "eu_directive": pt_config["late_payment_directive"],
            "allowed_terms": allowed,
            "compliant": is_allowed and not exceeds_limit,
        }
    )


@tool
def check_contract_clauses(contract_json: str) -> str:
    """
    Review a contract draft for mandatory clauses: force majeure, dispute resolution, governing law.
    contract_json: JSON string representing the contract terms.
    """
    regs = _regs()
    mandatory = regs["mandatory_contract_clauses"]

    try:
        contract = json.loads(contract_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON provided."})

    issues = []
    flags = []

    terms = contract.get("terms", {})

    if mandatory["force_majeure"] and not terms.get("force_majeure", False):
        issues.append("Missing force majeure clause (mandatory).")

    dr = terms.get("dispute_resolution", "")
    if dr not in mandatory["dispute_resolution"]:
        flags.append(f"Dispute resolution '{dr}' is non-standard. Recommended: ICC_Arbitration.")

    if not terms.get("governing_law"):
        issues.append("Governing law not specified.")

    return json.dumps(
        {
            "issues": issues,
            "flags": flags,
            "force_majeure_present": terms.get("force_majeure", False),
            "dispute_resolution": dr,
            "governing_law": terms.get("governing_law", ""),
            "compliant": len(issues) == 0,
        }
    )


LEGAL_TOOLS = [
    validate_incoterm,
    check_applicable_tariffs,
    check_carbon_compliance,
    validate_payment_terms,
    check_contract_clauses,
]
