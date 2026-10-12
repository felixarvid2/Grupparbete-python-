# Hämtar listan med alla regler från rules.py
from rules import ALL_RULES
# Hämtar funktionen som skriver rapporten från report.py
from report import print_report


# Funktion som granskar en enda config-fil
def audit_file(path):
    """Läser en config-fil och kör alla regler. Returnerar en lista med fynd."""
    # Öppnar filen för läsning; "with" stänger den automatiskt när vi är klara
    with open(path) as f:
        # Läser hela filen och delar upp den i rader
        lines = f.read().splitlines()   # en sträng per rad

    # Tom lista där alla fynd samlas
    findings = []
    # Går igenom alla regler, en i taget
    for rule in ALL_RULES:
        # Kör regeln på raderna och går igenom de problem den returnerar
        for problem in rule(lines):     # tom lista = regeln är OK
            # Sparar fyndet som ett par: (regelns namn, problemtexten)
            findings.append((rule.__name__, problem))
    # Lämnar tillbaka alla fynd till den som anropade funktionen
    return findings


# Koden under körs bara när man startar den här filen direkt (python auditor.py)
if __name__ == "__main__":
    # Granskar exempelfilen och sparar fynden
    findings = audit_file("samples/bad_router.cfg")
    # Skriver rapporten i terminalen och i tests/report.txt
    print_report(findings)