# report.py - gör en läsbar rapport av fynden från auditor.py.
#
# auditor.py ger oss en lista med fynd. Varje fynd är ett par:
#   (regelnamn, problem)
# t.ex. ("rule_ntp", "No NTP server configured ('ntp server ...')")
# Listan innehåller BARA regler som hittade fel.

# Hämtar listan med alla regler från rules.py
from rules import ALL_RULES  # regler som finns i rules.py


# Hjälpfunktion som skriver en rad på två ställen samtidigt
def write_line(f, text):
    """Skriver en rad både i terminalen och i rapportfilen."""
    # Skriver texten i terminalen
    print(text)
    # Skriver samma text i filen, med radbrytning (\n) på slutet
    f.write(text + "\n")


# Huvudfunktionen: bygger och skriver ut rapporten
def print_report(findings, filename="tests/report.txt"):
    """Skriver rapporten i terminalen och sparar den i en .txt-fil.

    Returnerar antal regler som fick fel (0 = allt var bra).
    """
    # Räknare som börjar på 0 och ökar för varje regel som fick fel
    failed = 0  # räknar hur många regler som fick fel

    # "w" = write, skriver över filen om den redan finns
    # encoding="utf-8" gör att å, ä och ö blir rätt i filen
    # Öppnar rapportfilen för skrivning; "with" stänger den automatiskt när vi är klara
    with open(filename, "w", encoding="utf-8") as f:

        # Gå igenom ALLA regler, så att även godkända regler syns i rapporten
        for rule in ALL_RULES:
            # Hämtar regelns namn som text, t.ex. "rule_ntp"
            name = rule.__name__

            # Plocka ut de problem som hör till just den här regeln
            # Tom lista som fylls med den här regelns problem
            problems = []
            # Går igenom alla fynd (varje fynd är ett par: regelnamn och problem)
            for rule_name, problem in findings:
                # Hör fyndet till regeln vi tittar på just nu?
                if rule_name == name:
                    # Lägger till problemtexten i listan
                    problems.append(problem)

            # Finns det minst ett problem för regeln?
            if problems:
                # Räknar upp antalet regler som fick fel
                failed += 1
                # Skriver rubrikraden "FEL" med regelns namn
                write_line(f, f"FEL  {name}")
                # Går igenom regelns problem
                for problem in problems:
                    # Skriver varje problem på en egen rad med ett streck framför
                    write_line(f, f"       - {problem}")
            # Annars hittade regeln inga fel
            else:
                # Skriver raden "OK" med regelns namn
                write_line(f, f"OK   {name}")

        # Totalt antal regler som finns
        total = len(ALL_RULES)
        # Skriver sammanfattningen, t.ex. "4/6 regler godkända" (\n ger en tom rad före)
        write_line(f, f"\n{total - failed}/{total} regler godkända")

    # Lämnar tillbaka antalet regler som fick fel (0 = allt var bra)
    return failed