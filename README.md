# MPO 5C — jednoduchá verzia

Python 3.10+, bez inštalácie ďalších knižníc. Rozbaľte archív a otvorte priečinok `mpo_simple` v PyCharme. Pôvodný Google Docs nebol zmenený.

## Spustenie

**Spustite `parser.py`** — vykoná obe metódy, vysvetlí rozhodnutia v konzole a zobrazí porovnanie:

```bash
python parser.py
```

**Spustite `test.py`**, ak chcete overiť pravidlá a očakávané výsledky:

```bash
python test.py
```

V PyCharme stačí otvoriť príslušný súbor a stlačiť Run. Ak potrebujete iba jeden algoritmus, spustite `main_greedy.py` alebo `main_custom.py`. Na Linuxe/macOS sa príkaz môže volať `python3`, vo Windows je dostupný aj `py`.

## Čo obsahuje priečinok

| Súbor | Účel |
|---|---|
| `main_greedy.py` | Najbližší obchod → nákup všetkého chýbajúceho |
| `main_custom.py` | Zlepšenie plánu z každého počiatočného obchodu → výber najlepšieho výsledku |
| `parser.py` | Čítanie CSV, spoločné pravidlá hodnotenia, zrozumiteľný výpis a porovnanie |
| `test.py` | 12 automatických kontrol; výsledky neukladá na disk |
| `products.csv` | 48 ponúk: produkt, obchod, balenie, cena, zásoba a zľava |
| `shopping_list.csv` | 12 požadovaných produktov a ich množstvá |
| `stores.csv` | Modelové poradie blízkosti obchodov a náklady na ich návštevu |
| `result_greedy.json` | Posledný výsledok greedy |
| `result_custom.json` | Posledný výsledok custom |

Ďalšie pracovné priečinky, generátor databázy ani samostatné súbory `model.py`/`baseline.py` nie sú potrebné. Dva JSON súbory sa pri spustení prepíšu; nové súbory výsledkov nepribúdajú. JSON netreba čítať: plán, dôvody rozhodnutí a sumy sú viditeľné v konzole. Python môže automaticky vytvoriť pomocný priečinok `__pycache__`; nejde o dáta projektu.

## Ako nakupuje greedy

Poradie blízkosti je zadané v `stores.csv`: Fresh — 1, Lidl/Kaufland — 2, Tesco — 3. Pri zhode rozhoduje názov podľa abecedy. Algoritmus ide do najbližšieho ešte neposúdeného obchodu s potrebnými dostupnými produktmi a nakúpi všetko, čo môže pokryť zostávajúci zoznam. Pri nedostatku zásob pokračuje v ďalšom obchode.

Ceny produktov neporovnáva. V našich dátach má Fresh všetko potrebné, preto greedy dokončí nákup v ňom. `proximity_rank` je modelové poradie blízkosti, nie vzdialenosť v kilometroch. Bez vzdialeností medzi všetkými bodmi tento baseline nepočíta skutočnú najkratšiu trasu.

## Ako nakupuje custom

1. Vypočíta cenu celého požadovaného nákupu v každom obchode **so zohľadnením celých balení a dopravy**. Porovnáva sa celková suma, nie priemerná cena produktov.
2. Každý obchod, ktorý sám pokryje celý zoznam, použije ako samostatný počiatočný plán. **Zlepšuje každý plán nezávisle**, nielen plán z najlacnejšieho počiatočného obchodu. Ak žiadny obchod nepokryje zoznam, použije počiatočný plán greedy.
3. Pre každý cieľový obchod hľadá kategórie, ktorých nákup je v ňom lacnejší než v aktuálnom pláne. Počíta cenu celého potrebného množstva; presúva celú kategóriu, nie jednotlivé ľubovoľné balenie. Kontroluje zásoby.
4. Kladné úspory pre cieľový obchod sčíta. Rozdiely zoradí od najväčšieho po najmenší na vysvetlenie rozhodnutia.
5. Vytvorí skúšobný plán, opäť ho overí a prepočíta dopravu. Vzorec: **čistá úspora = pôvodná celková cena − nová celková cena**. Zohľadní pridanie aj zrušenie návštev.
6. Zo všetkých posúdených obchodov vyberie presun s najväčšou kladnou čistou úsporou. Opakuje vyhľadávanie do zastavenia. Nakoniec porovná výsledky všetkých počiatočných plánov a vyberie najlacnejší prípustný výsledok.

Ak na káve ušetríme 2 € a na dvoch baleniach mlieka ďalšie 1 €, celková úspora je 3 €. Pri dodatočných nákladoch na cestu 2 € zostáva výhoda 1 €. Jednotlivé nákupy by cestu nemuseli zaplatiť, preto sa ich úspory sčítajú. Práve tento prípad overuje `test.py`.

V dodanej konfigurácii stojí návšteva Lidla a Kauflandu **spolu 2 €**, Fresh stojí 0 € a Tesco pridáva 4 €. Presun z Lidla do Kauflandu preto nepridáva náklady na dopravu. Ak sa majú platiť samostatne, zadajte im rozdielne `travel_zone` v `stores.csv`:

```csv
Lidl,2,lidl,200
Kaufland,2,kaufland,200
```

Návšteva oboch potom stojí 4 €. Druhý stĺpec určuje iba poradie blízkosti.

## Skutočné porovnanie

Výsledky pri spoločnej dopravnej zóne Lidl/Kaufland:

| Metóda | Produkty | Doprava | Celková suma |
|---|---:|---:|---:|
| Greedy | 54,31 € | 0,00 € | **54,31 €** |
| Custom | 40,21 € | 2,00 € | **42,21 €** |

Oba plány pokrývajú zoznam. Rozdiel je **12,10 €**.

Custom zlepší každý počiatočný nákup samostatne. Zo štartov Fresh, Kaufland a Lidl dosiahne 42,21 €, zo štartu Tesco 46,21 €. Napríklad počiatočný plán Lidl za 44,00 € zlepší presunom coly, mlieka, čokolády a chleba do Kauflandu. Úspora na produktoch je 1,79 €, dodatočná doprava 0 € a výsledok 42,21 €. Dôvody a nákupy každého štartu sa zobrazujú pri spustení. Pri samostatnom účtovaní Lidla a Kauflandu bol overený výsledok custom 43,29 €.

Ide o žravé lokálne zlepšovanie podľa čistej úspory s viacerými počiatočnými plánmi. Nezaručuje globálne minimum: napríklad viacero presunov môže byť výhodných iba spoločne. Metóda posudzuje presun do jedného obchodu za krok, preto môže takýto variant prehliadnuť. Nepresúva ani kategórie so zdražením produktov, hoci úplné zrušenie návštevy pôvodného obchodu by mohlo ušetriť dopravu. Počet balení volí minimálny na pokrytie potreby; dodatočné balenia výhradne kvôli zľave nepreberá. Porovnanie s najbližším Freshom ukazuje výsledok na jednej tabuľke, nie prevahu na všetkých možných dátach.

## Dáta a pravidlá

- Zdroj cien: [tabuľka zo Zadania 2](https://docs.google.com/document/d/1LSuWJjTs4z0TorBknQc0_Tzr4SbxwWkwd2tZlubYXMU), prečítaná 22. 11. 2026. Ide o dáta dokumentu, nie o nové aktuálne ceny obchodov.
- V `products.csv` jeden riadok predstavuje jednu kategóriu v jednom obchode. Pre jednoduchosť je podporovaná jedna ponuka takejto dvojice. Ceny sú v celých centoch, množstvá v gramoch, mililitroch alebo kusoch.
- Pri cenách za kg sú prijaté modelové balenia: ryža a kuracie filé — 1000 g, paradajky — 500 g. Pol kilogramu paradajok v Lidli/Kauflande je zaokrúhlený na 120/130 centov. Veľkosti sú predpoklady, nie potvrdené balenia. Označuje ich pole `note`.
- Prázdne `stock_packages` znamená dostatočnú modelovú zásobu; `0` znamená nedostupný produkt. Záporné a neceločíselné počty balení sú zakázané. Prebytok kvôli veľkosti balenia je povolený.
- `price_cents` je cena balenia, ktorá už zahŕňa pevnú akciovú cenu, ak bola v tabuľke. Neznáme podmienky kariet sa nevyhodnocujú. Voliteľné `buy_n` a `pay_m` umožňujú zadať akciu „3 za cenu 2“; v základných dátach sú prázdne.
- `deposit_cents` je samostatný záloh za každé balenie; aktuálne je 0, pretože pôvodná tabuľka zálohy neurčuje. Vrátenie zálohu sa nemodeluje.
- Rozpočet, otváracie hodiny a maximálny počet obchodov v tejto jednoduchej verzii nie sú obmedzené.
- Kandidát je slovník `{offer_id: počet_balení}`. Neuvedené ponuky majú počet 0. `evaluate()` iba overuje a počíta; algoritmy plán vytvárajú a menia. Neprípustný plán dostane `score_cents = null`; nízka cena neúplného zoznamu sa nepovažuje za úspech.

Po zmene cien sa môžu očakávané sumy v teste `test_actual_results` oprávnene zmeniť: treba ich prepočítať a aktualizovať. Väčšina ostatných testov používa malé nezávislé príklady.

Po zavedení viacerých štartov je jedno očakávanie zastarané: `test_custom_can_stop_before_global_optimum` očakáva 2000 centov, nová verzia však nájde lepší plán za 1900 centov. Tento test zatiaľ zlyhá, ostatných 11 prechádza; súbor `test.py` nebol upravený.

Dve porovnávané metódy sú implementované. Na finálnu požiadavku „baseline + dva prístupy“ bude neskôr potrebný ešte jeden prístup. Tretí algoritmus zatiaľ nebol pridaný.
