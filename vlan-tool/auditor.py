from rules import ALL_RULES
from report import print_report


def audit_file(path):
    """Läser en config-fil och kör alla regler. Returnerar en lista med fynd."""
    with open(path) as f:
        lines = f.read().splitlines()   # en sträng per rad

    findings = []
    for rule in ALL_RULES:
        for problem in rule(lines):     # tom lista = regeln är OK
            findings.append((rule.__name__, problem))
    return findings


if __name__ == "__main__":
    findings = audit_file("samples/bad.cfg")
    print_report(findings)