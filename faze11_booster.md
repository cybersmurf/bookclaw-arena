# Fáze 11: Booster Simulace (Zřetězené Hádanice a Odkazovací Kontext)
Uživatel si vyžádal zvýšení dynamičnosti simulace. Interakce v podobě kritiky by neměla být pouze jednosměrným pinkáním. Spisovatelé a Kritici budou mít nově prostor pro dvě repliky v jednom kole!

- [ ] Zřetězení obhajob `agent.py`: Upravit krok "Obhajoba autora" a "Finální verdikt kritika" tak, aby proběhly ve 2 plných smyčkách. Reálně S obhajuje, K hodnotí a odvětí, S znovu reaguje na nové výtky, a K vynáší super-finální verdikt s přihlédnutím k ústupkům.
- [ ] Změna propisování obhajob do databáze (z jednoho stringu do konverzačního listu/JSON formátu v tabulce `Review`).
- [ ] Vzájemné odkazování kritiků (Booster 1): Při hodnocení získají agilní Kritici i Čtenáři k dispozici JSON seznam VŠECH doposud vytvořených recenzí k dané povídce od ostatních kritiků v místnosti. Znalost "konkurenčních recenzí" do promptu umožní kritikům potvrzovat se navzájem nebo jít do argumentačního sporu.
- [ ] Odkazování čtenářů: Rozšiřit Prompt pro Čtenáře. Čtenáři si před vygenerováním reakce pročtou hodnocení kritiků i samotné dílo. Dozví se tak, zda je příběh "přijímán odbornou veřejností", což ovlivní jejich verdikt Hlasu Lidu.
- [ ] Update uživatelského rozhraní `index.html`: Vyrobit rekurzivní renderování konverzací mezi Spisovateli a Kritiky, aby uživatel jasně viděl chatboxovou historii jejich hádek.
