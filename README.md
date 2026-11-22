# MPO 5C

Python 3.11+, bez inštalácie ďalších knižníc. Rozbaľte archív a otvorte priečinok `mpo_simple` v PyCharme.

## Spustenie

**Spustite `parser.py`** — vykoná všetky tri metódy, vysvetlí rozhodnutia v konzole a zobrazí porovnanie:

```bash
python parser.py
```

**Spustite `test.py`**, ak chcete overiť pravidlá a očakávané výsledky:

```bash
python test.py
```

Samostatne možno spustiť `main_greedy.py`, `main_custom.py` alebo `main_exact.py`. Na Linuxe/macOS sa príkaz môže volať `python3`, vo Windows je dostupný aj `py`.

## Čo obsahuje priečinok

| Súbor | Účel |
|---|---|
| `main_greedy.py` | Najbližší obchod → nákup všetkého chýbajúceho |
| `main_custom.py` | Lokálne zlepšovanie od najlacnejšieho úplného nákupu v jednom obchode |
| `main_exact.py` | Presný výpočet pre všetky kombinácie dopravných zón |
| `parser.py` | Čítanie CSV, spoločné pravidlá hodnotenia, zrozumiteľný výpis a porovnanie |
| `test.py` | 13 automatických kontrol; výsledky neukladá na disk |
| `products.csv` | 48 ponúk: produkt, obchod, balenie, cena, zásoba a zľava |
| `shopping_list.csv` | 12 požadovaných produktov a ich množstvá |
| `stores.csv` | Modelové poradie blízkosti obchodov a náklady na ich návštevu |
| `result_greedy.json` | Posledný výsledok greedy |
| `result_custom.json` | Posledný výsledok custom |
| `result_exact.json` | Výsledok exact vytvorený pri spustení |

## Ako nakupuje greedy

Poradie blízkosti je zadané v `stores.csv`: Fresh — 1, Lidl/Kaufland — 2, Tesco — 3. Pri zhode rozhoduje názov podľa abecedy. Algoritmus ide do najbližšieho ešte neposúdeného obchodu s potrebnými dostupnými produktmi a nakúpi všetko, čo môže pokryť zostávajúci zoznam. Pri nedostatku zásob pokračuje v ďalšom obchode.

Ceny produktov neporovnáva. V našich dátach má Fresh všetko potrebné, preto greedy dokončí nákup v ňom. `proximity_rank` je modelové poradie blízkosti, nie vzdialenosť v kilometroch. Bez vzdialeností medzi všetkými bodmi tento baseline nepočíta skutočnú najkratšiu trasu.

## Ako nakupuje custom

1. Vypočíta cenu celého požadovaného nákupu v každom obchode **so zohľadnením celých balení a dopravy**. Porovnáva sa celková suma, nie priemerná cena produktov.
2. Začne najlacnejším plánom z obchodov, ktoré samy pokryjú celý zoznam. Ak žiadny obchod nepokryje zoznam, použije počiatočný plán greedy.
3. Pre každý cieľový obchod hľadá kategórie, ktorých nákup je v ňom lacnejší než v aktuálnom pláne. Počíta cenu celého potrebného množstva; presúva celú kategóriu, nie jednotlivé ľubovoľné balenie. Kontroluje zásoby.
4. Kladné úspory pre cieľový obchod sčíta. Rozdiely zoradí od najväčšieho po najmenší na vysvetlenie rozhodnutia.
5. Vytvorí skúšobný plán, opäť ho overí a prepočíta dopravu. Vzorec: **čistá úspora = pôvodná celková cena − nová celková cena**. Zohľadní pridanie aj zrušenie návštev.
6. Zo všetkých posúdených obchodov vyberie presun s najväčšou kladnou čistou úsporou. Opakuje vyhľadávanie, kým žiadny skúšaný presun nezníži celkovú cenu.

Ak na káve ušetríme 2 € a na dvoch baleniach mlieka ďalšie 1 €, celková úspora je 3 €. Pri dodatočných nákladoch na cestu 2 € zostáva výhoda 1 €. Jednotlivé nákupy by cestu nemuseli zaplatiť, preto sa ich úspory sčítajú. Práve tento prípad overuje `test.py`.

V dodanej konfigurácii stojí návšteva Lidla a Kauflandu **spolu 2 €**, Fresh stojí 0 € a Tesco pridáva 4 €. Presun z Lidla do Kauflandu preto nepridáva náklady na dopravu.

```csv
Lidl,2,lidl,200
Kaufland,2,kaufland,200
```

Návšteva oboch potom stojí 4 €. Druhý stĺpec určuje iba poradie blízkosti.

## Ako nakupuje exact

Metóda prejde všetky neprázdne kombinácie dopravných zón. Pre každú kombináciu nájde najlacnejší nákup potrebného množstva každej kategórie pomocou dynamického programovania. Môže kombinovať balenia z viacerých obchodov, zohľadňuje zásoby a akcie. Hodnotiaca funkcia pripočíta cenu skutočne využitých zón. Najlacnejší úplný plán je globálnym minimom v zadanom modeli.

Pri troch zónach metóda vyhodnotí sedem kombinácií. Počet kombinácií rastie exponenciálne s počtom zón.

## Skutočné porovnanie

Výsledky pri spoločnej dopravnej zóne Lidl/Kaufland:

| Metóda | Produkty | Doprava | Celková suma |
|---|---:|---:|---:|
| Greedy | 54,31 € | 0,00 € | **54,31 €** |
| Custom | 40,21 € | 2,00 € | **42,21 €** |
| Exact | 40,21 € | 2,00 € | **42,21 €** |

Všetky tri plány pokrývajú zoznam. Custom aj exact ušetria oproti greedy **12,10 €**.

Custom začne nákupom v Lidli za 44,00 € a presunie colu, mlieko, čokoládu a chlieb do Kauflandu. Úspora na produktoch je 1,79 €, dodatočná doprava 0 € a výsledok 42,21 €.

Custom v jednom kroku posudzuje presun do jedného obchodu a vyberá len kategórie s lacnejšími produktmi. V samostatnom príklade v `test_custom_can_stop_before_global_optimum` skončí custom na 20,00 €, kým exact dosiahne 19,00 € spojením dvoch presunov do spoločnej zóny.

## Dáta a pravidlá

- V `products.csv` jeden riadok predstavuje jednu kategóriu v jednom obchode. Pre jednoduchosť je podporovaná jedna ponuka takejto dvojice. Ceny sú v celých centoch, množstvá v gramoch, mililitroch alebo kusoch.
- Pri cenách za kg sú prijaté modelové balenia: ryža a kuracie filé — 1000 g, paradajky — 500 g. Pol kilogramu paradajok v Lidli/Kauflande je zaokrúhlený na 120/130 centov. Veľkosti sú predpoklady, nie potvrdené balenia. Označuje ich pole `note`.
- Prázdne `stock_packages` znamená dostatočnú modelovú zásobu; `0` znamená nedostupný produkt. Záporné a neceločíselné počty balení sú zakázané. Prebytok kvôli veľkosti balenia je povolený.
- `price_cents` je cena balenia, ktorá už zahŕňa pevnú akciovú cenu, ak bola v tabuľke. Neznáme podmienky kariet sa nevyhodnocujú. Voliteľné `buy_n` a `pay_m` umožňujú zadať akciu „3 za cenu 2“; v základných dátach sú prázdne.
- `deposit_cents` je samostatný záloh za každé balenie; aktuálne je 0, pretože pôvodná tabuľka zálohy neurčuje. Vrátenie zálohu sa nemodeluje.
- Rozpočet, otváracie hodiny a maximálny počet obchodov v tejto jednoduchej verzii nie sú obmedzené.
- Kandidát je slovník `{offer_id: počet_balení}`. Neuvedené ponuky majú počet 0. `evaluate()` iba overuje a počíta; algoritmy plán vytvárajú a menia. Neprípustný plán dostane `score_cents = null`; nízka cena neúplného zoznamu sa nepovažuje za úspech.
