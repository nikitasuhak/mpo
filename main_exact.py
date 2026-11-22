"""Presný výpočet pre model nákupu so zdieľanými dopravnými zónami."""

from itertools import combinations

from parser import evaluate, load_data, package_count, purchase_cost, show_and_save


def cheapest_category_plan(offers, required):
    """Pre každé pokryté množstvo uchová najlacnejší plán."""
    states = {0: (0, {})}
    for offer in offers:
        size = offer["package_quantity"]
        limit = package_count(required, size)
        buy = offer["buy_n"]
        if buy is not None:
            # Cena môže klesnúť pri dokončení ďalšej akciovej skupiny.
            limit = package_count(limit, buy) * buy
        stock = offer["stock_packages"]
        if stock is not None:
            limit = min(limit, stock)
        updated = states.copy()
        for count in range(1, limit + 1):
            cost = purchase_cost(offer, count)
            for quantity, (previous_cost, plan) in states.items():
                covered = min(required, quantity + count * size)
                total = previous_cost + cost
                if covered not in updated or total < updated[covered][0]:
                    updated[covered] = total, {**plan, offer["offer_id"]: count}
        states = updated
    return states[required][1] if required in states else None


def exact(data):
    zone_by_store = {name: store["travel_zone"] for name, store in data["stores"].items()}
    zones = sorted(set(zone_by_store.values()))
    offers_by_category = {category: [] for category in data["shopping"]}
    for offer in data["products"]:
        offers_by_category[offer["category_id"]].append(offer)

    best_plan, best_cost = {}, None
    checked = 0
    for size in range(1, len(zones) + 1):
        for allowed in combinations(zones, size):
            checked += 1
            plan = {}
            for category, requirement in data["shopping"].items():
                offers = [offer for offer in offers_by_category[category]
                          if zone_by_store[offer["store_id"]] in allowed]
                category_plan = cheapest_category_plan(offers, requirement["required_quantity"])
                if category_plan is None:
                    break
                plan.update(category_plan)
            else:
                cost = evaluate(data, plan)["score_cents"]
                if cost is not None and (best_cost is None or cost < best_cost):
                    best_plan, best_cost = plan, cost

    steps = [f"Preskúmané kombinácie dopravných zón: {checked}."]
    if best_cost is None:
        steps.append("Z dostupných zásob sa celý zoznam nedá pokryť.")
    else:
        steps.append(f"Najnižšia celková cena v zadanom modeli: {best_cost / 100:.2f} €.")
    return best_plan, steps


if __name__ == "__main__":
    data = load_data()
    plan, steps = exact(data)
    result = show_and_save(data, "exact", plan, steps)
    raise SystemExit(0 if result["feasible"] else 2)
