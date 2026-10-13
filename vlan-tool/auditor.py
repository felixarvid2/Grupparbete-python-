from rules import ALL_RULES
from report import print_report


def audit_file(path):
    """Läser en config-fil och kör alla regler. Returnerar en lista med fynd."""
    # "with" stänger filen automatiskt när vi är klara
    with open(path) as f:
        lines = f.read().splitlines()   # en sträng per rad

    findings = []
    for rule in ALL_RULES:
        for problem in rule(lines):     # tom lista = regeln är OK
            # Varje fynd är ett par: (regelns namn, problemtexten)
            findings.append((rule.__name__, problem))
    return findings


# Körs bara när man startar den här filen direkt (python auditor.py)
if __name__ == "__main__":
    findings = audit_file("samples/good.cfg")
    print_report(findings)