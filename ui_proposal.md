# Nápady na Vizuální Vylepšení (BookClaw 2.0)

Kódová a "mozková" část Arény nám aktuálně šlape náramně. Tady jsou nápady, co bychom mohli podniknout s vizuální částí ve `Vue.js + Tailwind` (`index.html`), abychom ze strohé stránky udělali zážitek blížící se interaktivní herní simulaci:

## 1. Dark Mode a "Cyberpunk/Magic" Téma Arény
Aktuálně máme čistý korporátní `bg-slate-50`. To se k drsné autorské aréně nehodí. 
- Přepneme hlavní UI do tmavých odstínů (`bg-slate-900`, `text-slate-200`).
- Autorům sci-fi dáme neonově modré glow efekty karet, zatímco autorům fantasy teplé zlaté a karmínové stíny. Rozlišíme je i vizuálně silněji, než jen malou "badge" značkou.

## 2. Plynulé animace a Skutečný "Kanban" povídek
Ačkoliv máme v pravém panelu výpis napsaných povídek s akordeonem pro rozbalování, chybí tam "drive".
- Použít Vue `<transition-group>` pro animovaný propad a objevení se zbrusu nové povídky (nebo recenze). Když do databáze dorazí nový text od agenta, karta by měla plynule, s efektem mírného "odlesku", sklouznout na stránku, místo vizuálního šoku při `fetchData`.

## 3. "Live" psací konzole pro Status orchestrátoru
Status (aktuální činnost) agentů teď bliká nahoře v jejich kartě jako úhoz ("Píše povídku...").
- Místo obyčejného textu můžeme pod ovládacím panelem (kde se volí kola) vyčlenit maticovou konzoli "Server Logs". Tam budou řádky ze zprávy orchestrátoru plynule "přitékat" se zeleným textem stylizované jako starý terminál, což uživateli dá maximální pocit transparentnosti procesu tvorby i bez otevírání skutečné konzole.

## 4. Analýza nálady a skóre vizualizací (Evoluční Grafy)
- Máme data o tom, jak Kritici hodnotili autory a jak autoři modifikují svůj System prompt (mají paměť a skóre).
- S integrací knihovny jako **Chart.js** nebo ApexCharts bychom mohli u každého autora místo textového "System Prompt" vypisovat malý radarový graf ukazující jeho žánrové kvality vůči kritikům (např. *Gramatika*, *Stylika*, *Dodržování kánonu*), které by s každým kolem přibývaly a ubývaly jako expy u postavy v RPG!
