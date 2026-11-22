"""Baseline: najbližší obchod podľa zadaného poradia, nákup všetkého chýbajúceho."""

from parser import load_data, package_count, show_and_save


def greedy(data):
    remaining = {name: row["required_quantity"] for name, row in data["shopping"].items()}
    plan, steps = {}, []
    stores = sorted(data["stores"], key=lambda name: (data["stores"][name]["proximity_rank"], name))
    for store in stores:
        if all(quantity <= 0 for quantity in remaining.values()):
            break
        offers = [p for p in data["products"] if p["store_id"] == store
                  and remaining[p["category_id"]] > 0 and p["stock_packages"] != 0]
        if not offers:
            continue
        steps.append(f"Vyberám {store}: najbližší zostávajúci obchod podľa proximity_rank.")
        for product in offers:
            category = product["category_id"]
            count = package_count(remaining[category], product["package_quantity"])
            if product["stock_packages"] is not None:
                count = min(count, product["stock_packages"])
            plan[product["offer_id"]] = count
            remaining[category] -= count * product["package_quantity"]
        steps.append(f"V {store} kupujem dostupné celé balenia na pokrytie chýbajúcich potrieb.")
    if any(quantity > 0 for quantity in remaining.values()):
        steps.append("Všetky potreby sa nepodarilo pokryť; kontrola vypíše nedostatky.")
    else:
        steps.append("Zoznam je pokrytý. Ďalšie obchody nenavštevujem.")
    return plan, steps


if __name__ == "__main__":
    data = load_data()
    plan, steps = greedy(data)
    result = show_and_save(data, "greedy", plan, steps)
    raise SystemExit(0 if result["feasible"] else 2)
