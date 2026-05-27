#!/usr/bin/env python3
"""
Fetch amino acid data from USDA FoodData Central for common plant-based foods.
Uses the public DEMO_KEY (30 req/hour) — swap for a free API key at https://fdc.nal.usda.gov/api-key-signup.html
"""

import requests
import json
import time
import sys

API_KEY = "DEMO_KEY"
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# ── Food list (FDC IDs verified against FoodData Central Foundation/SR-Legacy) ──
FOODS = [
    # Soy-based
    {"name": "Firm Tofu",             "fdc_id": 172475, "category": "soy",     "emoji": "🫘", "serving": "100g block"},
    {"name": "Tempeh",                "fdc_id": 174272, "category": "soy",     "emoji": "🫘", "serving": "100g"},
    {"name": "Edamame (cooked)",      "fdc_id": 168411, "category": "soy",     "emoji": "🫛", "serving": "100g shelled"},
    {"name": "Soybeans (cooked)",     "fdc_id": 175237, "category": "soy",     "emoji": "🫘", "serving": "100g"},

    # Legumes
    {"name": "Red Lentils (cooked)",  "fdc_id": 172421, "category": "legume",  "emoji": "🟠", "serving": "100g"},
    {"name": "Chickpeas (cooked)",    "fdc_id": 173756, "category": "legume",  "emoji": "🟡", "serving": "100g"},
    {"name": "Black Beans (cooked)",  "fdc_id": 173735, "category": "legume",  "emoji": "⚫", "serving": "100g"},
    {"name": "Kidney Beans (cooked)", "fdc_id": 175197, "category": "legume",  "emoji": "🔴", "serving": "100g"},
    {"name": "Green Peas (cooked)",   "fdc_id": 170420, "category": "legume",  "emoji": "💚", "serving": "100g"},

    # Grains & pseudograins
    {"name": "Quinoa (cooked)",       "fdc_id": 168917, "category": "grain",   "emoji": "🌾", "serving": "100g"},
    {"name": "Oats (cooked)",         "fdc_id": 173904, "category": "grain",   "emoji": "🥣", "serving": "100g"},
    {"name": "Brown Rice (cooked)",   "fdc_id": 169704, "category": "grain",   "emoji": "🍚", "serving": "100g"},
    {"name": "Whole Wheat Bread",     "fdc_id": 172686, "category": "grain",   "emoji": "🍞", "serving": "1 slice (~30g)"},

    # Seeds
    {"name": "Hemp Seeds (hulled)",   "fdc_id": 170148, "category": "seed",    "emoji": "🌿", "serving": "30g (3 tbsp)"},
    {"name": "Chia Seeds",            "fdc_id": 170554, "category": "seed",    "emoji": "⚫", "serving": "28g (2 tbsp)"},
    {"name": "Pumpkin Seeds",         "fdc_id": 170556, "category": "seed",    "emoji": "🎃", "serving": "28g handful"},
    {"name": "Sunflower Seeds",       "fdc_id": 170563, "category": "seed",    "emoji": "🌻", "serving": "28g handful"},
    {"name": "Flaxseeds",             "fdc_id": 169414, "category": "seed",    "emoji": "🟤", "serving": "15g (1 tbsp)"},

    # Nuts & nut butters
    {"name": "Almonds",               "fdc_id": 170567, "category": "nut",     "emoji": "🥜", "serving": "28g handful"},
    {"name": "Peanuts",               "fdc_id": 172430, "category": "nut",     "emoji": "🥜", "serving": "28g handful"},
    {"name": "Cashews",               "fdc_id": 170162, "category": "nut",     "emoji": "🥜", "serving": "28g handful"},
    {"name": "Walnuts",               "fdc_id": 170187, "category": "nut",     "emoji": "🥜", "serving": "28g handful"},
    {"name": "Peanut Butter",         "fdc_id": 172470, "category": "nut",     "emoji": "🥜", "serving": "32g (2 tbsp)"},

    # Other plant proteins
    {"name": "Spirulina (dried)",     "fdc_id": 169578, "category": "algae",   "emoji": "💚", "serving": "10g (1 tbsp)"},
    {"name": "Nutritional Yeast",     "fdc_id": 2644203,"category": "other",   "emoji": "🟡", "serving": "15g (2 tbsp)"},

    # Vegetables (lower protein but included for completeness)
    {"name": "Broccoli (cooked)",     "fdc_id": 170379, "category": "veggie",  "emoji": "🥦", "serving": "100g"},
    {"name": "Spinach (cooked)",      "fdc_id": 170091, "category": "veggie",  "emoji": "🥬", "serving": "100g"},
    {"name": "Peas (green, cooked)",  "fdc_id": 170420, "category": "veggie",  "emoji": "💚", "serving": "100g"},

    # Vegetarian (not vegan)
    {"name": "Eggs (whole, large)",   "fdc_id": 171287, "category": "vegetarian", "emoji": "🥚", "serving": "50g (1 large)"},
    {"name": "Greek Yogurt (plain)",  "fdc_id": 170903, "category": "vegetarian", "emoji": "🥛", "serving": "170g (¾ cup)"},
    {"name": "Cottage Cheese",        "fdc_id": 173418, "category": "vegetarian", "emoji": "🧀", "serving": "113g (½ cup)"},
    {"name": "Cow's Milk (whole)",    "fdc_id": 171265, "category": "vegetarian", "emoji": "🥛", "serving": "244g (1 cup)"},
]

# ── Amino acid nutrient IDs in USDA FoodData Central ──
AA_NUTRIENT_IDS = {
    "tryptophan":    1210,  # also seen as 501
    "threonine":     1211,  # also seen as 502
    "isoleucine":    1212,  # also seen as 503
    "leucine":       1213,  # also seen as 504
    "lysine":        1214,  # also seen as 505
    "methionine":    1215,  # also seen as 506
    "cystine":       1216,  # also seen as 507
    "phenylalanine": 1217,  # also seen as 508
    "tyrosine":      1218,  # also seen as 509
    "valine":        1219,  # also seen as 510
    "histidine":     1221,  # also seen as 512
}

# Fallback IDs (older SR-legacy numbering)
AA_NUTRIENT_IDS_ALT = {
    "tryptophan":    501,
    "threonine":     502,
    "isoleucine":    503,
    "leucine":       504,
    "lysine":        505,
    "methionine":    506,
    "cystine":       507,
    "phenylalanine": 508,
    "tyrosine":      509,
    "valine":        510,
    "histidine":     512,
}

PROTEIN_IDS = {1003, 203}  # protein nutrient IDs


def fetch_food(fdc_id):
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key": API_KEY, "format": "full"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            print("  ⚠ Rate limited — sleeping 65s")
            time.sleep(65)
            return fetch_food(fdc_id)
        else:
            print(f"  ✗ HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def extract_nutrients(food_data):
    nutrients = food_data.get("foodNutrients", [])
    result = {}

    # Build a map: nutrient_id → amount (g per 100g)
    nmap = {}
    for n in nutrients:
        nutrient = n.get("nutrient", {})
        nid = nutrient.get("id")
        amount = n.get("amount")
        if nid is not None and amount is not None:
            nmap[nid] = amount

    # Protein
    protein_g = 0.0
    for pid in PROTEIN_IDS:
        if pid in nmap:
            protein_g = nmap[pid]
            break
    result["protein"] = round(protein_g, 2)

    # Amino acids — try primary IDs, fall back to legacy
    for aa, nid in AA_NUTRIENT_IDS.items():
        alt_nid = AA_NUTRIENT_IDS_ALT[aa]
        val = nmap.get(nid) or nmap.get(alt_nid) or 0.0
        result[aa] = round(val * 1000, 1)  # g → mg per 100g food

    return result


def main():
    print("Fetching amino acid data from USDA FoodData Central...\n")
    output = []

    for food in FOODS:
        fdc_id = food["fdc_id"]
        name = food["name"]
        print(f"  → {name} (FDC {fdc_id})")

        data = fetch_food(fdc_id)
        if not data:
            print(f"  ✗ Skipped (no data)")
            continue

        nutrients = extract_nutrients(data)
        protein = nutrients.get("protein", 0)
        leucine = nutrients.get("leucine", 0)

        print(f"     protein: {protein}g/100g  |  leucine: {leucine}mg/100g")

        record = {
            "name": name,
            "category": food["category"],
            "emoji": food["emoji"],
            "serving_hint": food["serving"],
            "fdc_id": fdc_id,
            "per100g": nutrients,
        }
        output.append(record)
        time.sleep(1.2)  # stay well within rate limits

    out_path = "amino_data.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(output)} foods to {out_path}")
    return output


if __name__ == "__main__":
    main()
