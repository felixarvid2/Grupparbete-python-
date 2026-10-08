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