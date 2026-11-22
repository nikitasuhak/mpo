"""Vlastná heuristika: najlacnejší celý nákup, potom najlepší čistý presun."""

from parser import evaluate, load_data, package_count, purchase_cost, show_and_save


def single_store_plan(data, store):
    """None znamená, že obchod sám nedokáže pokryť nákupný zoznam."""
    offers = {p["category_id"]: p for p in data["products"] if p["store_id"] == store}
    plan = {}
    for category, requirement in data["shopping"].items():
        product = offers.get(category)
        if product is None:
            return None
        count = package_count(requirement["required_quantity"], product["package_quantity"])
        if product["stock_packages"] is not None and count > product["stock_packages"]:
            return None
        plan[product["offer_id"]] = count
    return plan


def custom(data):
    steps, starts = [], []
    for store in sorted(data["stores"]):
        plan = single_store_plan(data, store)
        if plan is None:
            steps.append(f"{store}: samotný obchod nepokryje celý zoznam.")
            continue
        result = evaluate(data, plan)
        steps.append(f"Celý nákup v {store}: produkty {result['products_cents']/100:.2f} € "
                     f"+ doprava {result['travel_cents']/100:.2f} € "
                     f"= {result['total_cents']/100:.2f} €.")
        starts.append((result["total_cents"], store, plan))
    if starts:
        _, store, plan = min(starts, key=lambda row: (row[0], row[1]))
        steps.append(f"Začínam celým nákupom v {store}: najlacnejší prípustný jednomiestny plán.")
    else:
        # Výnimočný prípad: žiadny obchod nemá všetko. Zdieľame jednoduchý fallback.
        from main_greedy import greedy
        plan, _ = greedy(data)
        steps.append("Žiadny obchod nemá všetko; počiatočný plán vytvorí greedy.")
    current = evaluate(data, plan)
    if not current["feasible"]:
        steps.append("Počiatočný plán je neprípustný; zlepšovanie sa nespustí.")
        return plan, steps
    by_id = {p["offer_id"]: p for p in data["products"]}
    while True:
        best = None
        for store in sorted(data["stores"]):
            moves = []
            for target in data["products"]:
                if target["store_id"] != store:
                    continue
                category = target["category_id"]
                count = package_count(data["shopping"][category]["required_quantity"], target["package_quantity"])
                if target["stock_packages"] is not None and count > target["stock_packages"]:
                    continue
                previous = [identifier for identifier in plan if by_id[identifier]["category_id"] == category]
                old_cost = sum(purchase_cost(by_id[identifier], plan[identifier]) for identifier in previous)
                saving = old_cost - purchase_cost(target, count)
                if saving > 0:
                    moves.append((saving, target["offer_id"], count, previous, category))
            if not moves:
                continue
            # Najväčšie cenové rozdiely uvádzame prvé. Úspora sa sčíta za celý obchod.
            moves.sort(key=lambda move: (-move[0], move[1]))
            proposal = dict(plan)
            for _, identifier, count, previous, _ in moves:
                for old_identifier in previous:
                    proposal.pop(old_identifier)
                proposal[identifier] = count
            result = evaluate(data, proposal)
            net_saving = current["total_cents"] - result["total_cents"]
            if result["feasible"] and net_saving > 0:
                if best is None or net_saving > best[0]:
                    best = net_saving, store, proposal, result, moves
        if best is None:
            steps.append("Žiadny skúšaný presun kladných produktových úspor do jedného obchodu už neznižuje celkovú cenu.")
            break
        saving, store, proposal, result, moves = best
        product_saving = current["products_cents"] - result["products_cents"]
        travel_change = result["travel_cents"] - current["travel_cents"]
        details = ", ".join(f"{category}: {amount/100:.2f} €" for amount, _, _, _, category in moves)
        steps.append(f"Presúvam nákup do {store} ({details}). Úspora produktov {product_saving/100:.2f} € "
                     f"− zmena dopravy {travel_change/100:.2f} € = čistá úspora {saving/100:.2f} €.")
        plan, current = proposal, result
    return plan, steps


if __name__ == "__main__":
    data = load_data()
    plan, steps = custom(data)
    result = show_and_save(data, "custom", plan, steps)
    raise SystemExit(0 if result["feasible"] else 2)
