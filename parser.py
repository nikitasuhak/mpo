"""Čítanie CSV, spoločné pravidlá a porovnanie troch metód.

Spustenie tohto súboru vykoná všetky tri metódy. Pri importe iba sprístupní funkcie.
Peniaze: celé centy. Množstvá: gramy, mililitre alebo kusy podľa kategórie.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def load_data(directory=ROOT):
    """Jeden riadok products.csv = jedna ponuka produktu v jednom obchode."""
    directory = Path(directory)
    products = read_csv(directory / "products.csv")
    shopping = read_csv(directory / "shopping_list.csv")
    stores = read_csv(directory / "stores.csv")
    if not products or not shopping or not stores:
        raise ValueError("Všetky tri CSV musia obsahovať dáta")
    for rows, field in ((products, "offer_id"), (shopping, "category_id"), (stores, "store_id")):
        values = [row[field] for row in rows]
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError(f"Prázdne alebo duplicitné {field}")
    shopping = {row["category_id"]: row for row in shopping}
    stores = {row["store_id"]: row for row in stores}
    zones = {}
    for store in stores.values():
        for field in ("proximity_rank", "visit_cost_cents"):
            store[field] = int(store[field])
        if store["proximity_rank"] < 1 or store["visit_cost_cents"] < 0 or not store["travel_zone"]:
            raise ValueError("Neplatná blízkosť alebo doprava")
        zone, cost = store["travel_zone"], store["visit_cost_cents"]
        if zone in zones and zones[zone] != cost:
            raise ValueError("Obchody v spoločnej zóne musia mať rovnakú cenu návštevy")
        zones[zone] = cost
    for requirement in shopping.values():
        requirement["required_quantity"] = int(requirement["required_quantity"])
        if requirement["required_quantity"] <= 0 or requirement["unit"] not in {"g", "ml", "ks"}:
            raise ValueError("Neplatné požadované množstvo alebo jednotka")
    pairs = set()
    for product in products:
        pair = product["category_id"], product["store_id"]
        if pair in pairs:
            raise ValueError("Jednoduchá verzia povoľuje jednu ponuku kategórie na obchod")
        pairs.add(pair)
        if product["category_id"] not in shopping or product["store_id"] not in stores:
            raise ValueError("Neznámy produkt alebo obchod")
        if product["unit"] != shopping[product["category_id"]]["unit"]:
            raise ValueError("Nesúlad jednotiek")
        for field in ("package_quantity", "price_cents", "deposit_cents"):
            product[field] = int(product[field])
            if product[field] < 0:
                raise ValueError(f"Záporné {field}")
        if product["package_quantity"] == 0:
            raise ValueError("Prázdne balenie")
        for field in ("stock_packages", "buy_n", "pay_m"):
            product[field] = None if product[field] == "" else int(product[field])
        if product["stock_packages"] is not None and product["stock_packages"] < 0:
            raise ValueError("Záporná zásoba")
        buy, pay = product["buy_n"], product["pay_m"]
        if (buy is None) != (pay is None) or (buy is not None and not 0 <= pay < buy):
            raise ValueError("Neplatná akcia: vyžaduje 0 <= pay_m < buy_n")
    return {"products": products, "shopping": shopping, "stores": stores}


def package_count(quantity, package_size):
    """Zaokrúhlenie počtu celých balení nahor: 250 g / 500 g = 1 balenie."""
    return (quantity + package_size - 1) // package_size


def purchase_cost(product, count):
    paid = count
    if product["buy_n"] is not None:
        groups, rest = divmod(count, product["buy_n"])
        paid = groups * product["pay_m"] + rest
    return paid * product["price_cents"] + count * product["deposit_cents"]


def travel_cost(data, visited):
    """Spoločná zóna sa účtuje raz; Lidl + Kaufland spolu = 2 €."""
    zones = {}
    for name in visited:
        store = data["stores"][name]
        zones[store["travel_zone"]] = store["visit_cost_cents"]
    return sum(zones.values())


def evaluate(data, plan):
    """Plan je slovník {offer_id: počet balení}; neuvedené ponuky majú počet 0.

    Funkcia nič nenakupuje ani neopravuje. Iba overí plán a vypočíta náklady.
    score_cents=None znamená neprípustný plán, aj keď je čiastočná cena nízka.
    """
    products = {p["offer_id"]: p for p in data["products"]}
    errors, purchases = [], []
    bought = {category: 0 for category in data["shopping"]}
    visited = set()
    total_products = 0
    if not isinstance(plan, dict):
        return {"feasible": False, "errors": ["Plán musí byť slovník"], "score_cents": None,
                "products_cents": None, "travel_cents": None, "total_cents": None,
                "visited_stores": [], "coverage": [], "purchases": []}
    for identifier, count in plan.items():
        if identifier not in products:
            errors.append(f"Neznáma ponuka {identifier}")
            continue
        if type(count) is not int or count < 0:
            errors.append(f"{identifier}: počet musí byť celé nezáporné číslo")
            continue
        product = products[identifier]
        stock = product["stock_packages"]
        if stock is not None and count > stock:
            errors.append(f"{identifier}: prekročená zásoba {stock}")
        if count == 0:
            continue
        quantity = count * product["package_quantity"]
        cost = purchase_cost(product, count)
        bought[product["category_id"]] += quantity
        visited.add(product["store_id"])
        total_products += cost
        purchases.append({"offer_id": identifier, "product": product["category_id"],
                          "store": product["store_id"], "packages": count,
                          "package_size": product["package_quantity"],
                          "quantity": quantity, "unit": product["unit"], "cost_cents": cost})
    coverage = []
    for category, requirement in data["shopping"].items():
        needed = requirement["required_quantity"]
        got = bought[category]
        coverage.append({"product": category, "needed": needed, "bought": got,
                         "surplus": max(0, got - needed), "unit": requirement["unit"]})
        if got < needed:
            errors.append(f"{category}: chýba {needed - got} {requirement['unit']}")
    travel = travel_cost(data, visited)
    total = total_products + travel
    return {"feasible": not errors, "errors": errors,
            "score_cents": total if not errors else None,
            "products_cents": total_products, "travel_cents": travel, "total_cents": total,
            "visited_stores": sorted(visited), "coverage": coverage, "purchases": purchases}


def show_and_save(data, method, plan, steps, directory=ROOT):
    result = evaluate(data, plan)
    print(f"\n=== {method.upper()} ===")
    for step in steps:
        print(step)
    print("\nNákupný plán:")
    for item in result["purchases"]:
        print(f"  {item['store']:10} {item['product']:12} "
              f"{item['packages']} × {item['package_size']} {item['unit']} "
              f"= {item['cost_cents']/100:.2f} €")
    print(f"Produkty: {result['products_cents']/100:.2f} € | "
          f"Doprava: {result['travel_cents']/100:.2f} € | SPOLU: {result['total_cents']/100:.2f} €")
    print("Pravidlá: SPLNENÉ" if result["feasible"] else "Pravidlá: NESPLNENÉ")
    for error in result["errors"]:
        print("  ", error)
    output = Path(directory) / f"result_{method}.json"
    output.write_text(json.dumps({"method": method, "plan": plan, "steps": steps, **result},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    from main_greedy import greedy
    from main_custom import custom
    from main_exact import exact

    data = load_data()
    rows = {}
    for name, algorithm in (("greedy", greedy), ("custom", custom), ("exact", exact)):
        plan, steps = algorithm(data)
        rows[name] = show_and_save(data, name, plan, steps)
    print("\n=== POROVNANIE ===")
    for name, result in rows.items():
        if result["feasible"]:
            print(f"{name}: {result['total_cents']/100:.2f} €")
        else:
            print(f"{name}: neprípustný plán; cenu neporovnávame ako úspech")
    for baseline, method in (("greedy", "custom"), ("greedy", "exact"), ("custom", "exact")):
        first, second = rows[baseline]["score_cents"], rows[method]["score_cents"]
        if first is not None and second is not None:
            print(f"Rozdiel {baseline} − {method}: {(first - second) / 100:.2f} €")
