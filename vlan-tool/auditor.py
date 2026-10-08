from rules import ALL_RULES


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
    for rule_name, problem in audit_file("samples/good.cfg"):   # byt till .cfg som ska testas
        print(rule_name, "-", problem)
    print("Klar")