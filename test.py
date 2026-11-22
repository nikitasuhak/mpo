"""Kontrola pravidiel a známych výsledkov. Nevytvára žiadne súbory."""

import unittest

from parser import evaluate, load_data, package_count, purchase_cost, travel_cost
from main_greedy import greedy
from main_custom import custom
from main_exact import exact


def example(trip_cost=200):
    """Káva: 10/8 €, mlieko: 1/0,50 € × 2, ryža drahá v Lidli."""
    data = {"shopping": {"coffee": {"required_quantity": 250, "unit": "g"},
                         "milk": {"required_quantity": 2000, "unit": "ml"},
                         "rice": {"required_quantity": 1000, "unit": "g"}},
            "stores": {"Kaufland": {"proximity_rank": 1, "travel_zone": "K", "visit_cost_cents": 0},
                       "Lidl": {"proximity_rank": 2, "travel_zone": "L", "visit_cost_cents": trip_cost}},
            "products": []}
    for category, size, prices, unit in (("coffee", 250, (1000, 800), "g"),
                                        ("milk", 1000, (100, 50), "ml"),
                                        ("rice", 1000, (100, 1000), "g")):
        for store, price in zip(("Kaufland", "Lidl"), prices):
            data["products"].append({"offer_id": f"{category}_{store}", "category_id": category,
                                     "store_id": store, "package_quantity": size, "unit": unit,
                                     "price_cents": price, "deposit_cents": 0,
                                     "stock_packages": None, "buy_n": None, "pay_m": None})
    return data


class Tests(unittest.TestCase):
    def test_actual_results(self):
        data = load_data()
        for algorithm, expected in ((greedy, 5431), (custom, 4221), (exact, 4221)):
            plan, _ = algorithm(data)
            result = evaluate(data, plan)
            self.assertTrue(result["feasible"])
            self.assertEqual(result["total_cents"], expected)

    def test_coffee_and_two_milks_together_pay_for_trip(self):
        data = example()
        plan, _ = custom(data)
        self.assertEqual(plan["coffee_Lidl"], 1)
        self.assertEqual(plan["milk_Lidl"], 2)
        self.assertEqual(evaluate(data, plan)["total_cents"], 1200)
        self.assertEqual(evaluate(data, greedy(data)[0])["total_cents"], 1300)

    def test_expensive_trip_is_rejected(self):
        data = example(trip_cost=400)
        plan, _ = custom(data)
        self.assertEqual(evaluate(data, plan)["visited_stores"], ["Kaufland"])
        self.assertEqual(evaluate(data, plan)["total_cents"], 1300)

    def test_round_up_and_charge_whole_pack(self):
        self.assertEqual(package_count(250, 500), 1)
        self.assertEqual(package_count(2000, 1500), 2)
        product = example()["products"][0]
        product.update(package_quantity=500, price_cents=599)
        self.assertEqual(purchase_cost(product, package_count(250, 500)), 599)

    def test_shared_transport_cost(self):
        data = load_data()
        self.assertEqual(travel_cost(data, {"Lidl", "Kaufland"}), 200)
        self.assertEqual(travel_cost(data, {"Lidl", "Kaufland", "Tesco", "Fresh"}), 600)
        self.assertEqual(travel_cost(data, set()), 0)

    def test_incomplete_plan_is_invalid_even_if_free(self):
        result = evaluate(load_data(), {})
        self.assertFalse(result["feasible"])
        self.assertIsNone(result["score_cents"])
        self.assertEqual(result["total_cents"], 0)
        self.assertEqual(len(result["errors"]), 12)

    def test_bad_counts_and_unknown_product(self):
        data = load_data()
        identifier = data["products"][0]["offer_id"]
        for value in (-1, 0.5, True, "2"):
            self.assertFalse(evaluate(data, {identifier: value})["feasible"])
        self.assertFalse(evaluate(data, {"unknown": 1})["feasible"])
        self.assertFalse(evaluate(data, [1])["feasible"])

    def test_stock_shortage_is_reported(self):
        data = example()
        for product in data["products"]:
            if product["category_id"] == "coffee":
                product["stock_packages"] = 0
        for algorithm in (greedy, custom, exact):
            result = evaluate(data, algorithm(data)[0])
            self.assertFalse(result["feasible"])
            self.assertTrue(any("coffee" in error for error in result["errors"]))
        self.assertFalse(evaluate(data, {"coffee_Kaufland": 1})["feasible"])

    def test_split_stock_and_custom_fallback(self):
        data = example()
        data["shopping"]["coffee"]["required_quantity"] = 500
        for product in data["products"]:
            if product["category_id"] == "coffee":
                product["stock_packages"] = 1
        plan, steps = custom(data)
        self.assertTrue(evaluate(data, plan)["feasible"])
        self.assertEqual(plan["coffee_Kaufland"], 1)
        self.assertEqual(plan["coffee_Lidl"], 1)
        self.assertTrue(any("greedy" in step for step in steps))
        exact_plan, _ = exact(data)
        self.assertTrue(evaluate(data, exact_plan)["feasible"])
        self.assertEqual(exact_plan["coffee_Kaufland"], 1)
        self.assertEqual(exact_plan["coffee_Lidl"], 1)

    def test_discount_and_deposit(self):
        product = example()["products"][0]
        product.update(price_cents=100, buy_n=3, pay_m=2, deposit_cents=15)
        self.assertEqual(purchase_cost(product, 2), 230)
        self.assertEqual(purchase_cost(product, 3), 245)
        self.assertEqual(purchase_cost(product, 6), 490)

    def test_determinism(self):
        data = load_data()
        for algorithm in (greedy, custom, exact):
            self.assertEqual(algorithm(data), algorithm(data))

    def test_custom_can_stop_before_global_optimum(self):
        # Dva samostatne nevýhodné presuny sú spoločne výhodné v zdieľanej zóne.
        data = {"shopping": {"x": {"required_quantity": 1, "unit": "ks"},
                             "y": {"required_quantity": 1, "unit": "ks"}},
                "stores": {"A": {"proximity_rank": 1, "travel_zone": "a", "visit_cost_cents": 0},
                           "B": {"proximity_rank": 2, "travel_zone": "bc", "visit_cost_cents": 200},
                           "C": {"proximity_rank": 2, "travel_zone": "bc", "visit_cost_cents": 200}},
                "products": []}
        for store, prices in (("A", (1000, 1000)), ("B", (850, 2000)), ("C", (2000, 850))):
            for category, price in zip(("x", "y"), prices):
                data["products"].append({"offer_id": category + store, "category_id": category,
                                         "store_id": store, "package_quantity": 1, "unit": "ks",
                                         "price_cents": price, "deposit_cents": 0,
                                         "stock_packages": None, "buy_n": None, "pay_m": None})
        plan, _ = custom(data)
        self.assertEqual(evaluate(data, plan)["total_cents"], 2000)
        exact_plan, _ = exact(data)
        self.assertEqual(exact_plan, {"xB": 1, "yC": 1})
        self.assertEqual(evaluate(data, exact_plan)["score_cents"], 1900)

    def test_exact_can_buy_an_extra_pack_for_a_discount(self):
        data = example()
        data["shopping"] = {"coffee": {"required_quantity": 500, "unit": "g"}}
        product = data["products"][0]
        data["products"] = [product]
        product.update(price_cents=100, buy_n=3, pay_m=1, deposit_cents=10)
        plan, _ = exact(data)
        self.assertEqual(plan, {"coffee_Kaufland": 3})
        self.assertEqual(evaluate(data, plan)["score_cents"], 130)
        product["stock_packages"] = 2
        plan, _ = exact(data)
        self.assertEqual(plan, {"coffee_Kaufland": 2})
        self.assertEqual(evaluate(data, plan)["score_cents"], 220)


if __name__ == "__main__":
    unittest.main(verbosity=2)
