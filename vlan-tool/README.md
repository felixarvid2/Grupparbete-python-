Vi strukturerar grupparbetet hittills såhär:

Vi har generator.py som läser CSV och bygger en cisco konfig som text
rules.py är för reglerna, en funktion per regel
auditor.py läser en sparad konfig, kör alla regler och samlar avvikelser
report.py formaterar avvikelserna (terminal, textfil, csv/markdown)
main.py för kommandorader, t.ex. generate och audit

Två mappar:
samples/ <-här ska alla CSV filer samlas, just nu behöver vi 2st, "dhcp.csv" och "ports.csv"->
tests/ <-här ska loggarna genereras när vi kör auditor/generator/report->

Attila skriver just nu "dhcp.csv" och Patrik skriver "ports.csv"
Felix skriver på "main.py" och Jonathan skriver på "rules.py & auditor.py"

Uppdatering kl 12:44 2026-10-08

Attila har skrivit klart "dhcp.csv" samt korrigerat, pushat till /samples/ som planerat
Patrik har skrivir klart "ports.csv" men behöver korrigera några saker, väntar på gruppchatt accept så vi kan fortsätta kommunicera där, finns i /samples/ som planerat.
Felix håller på skriva "main.py" med tydlig kodning samt kommentarer
Jonathan har skrivit rules.py, auditor.py, good.cfg samt bad.cfg, försöker se till att allt kan förstås på den nivån vi har i python.

Det som fortfarande behövs:

Vi behöver generator.py som läser CSV och bygger CISCO IOS-konfig som text
report.py som läser avvikelserna genererade av auditor.py och skriver till ett text dokument

Uppdatering kl 13:35 2026-10-08

Klart:
report.py är klar och har kopplats ihop med auditor.py

Behövs göras:
Attila har börjat med generator.py, pushar sen när han är klar eller behöver hjälp.
Ports.csv behövs korrigeras när Patrik har tid.
good_router.cfg och bad_router.cfg behöver data så auditor.py kan läsa dem.