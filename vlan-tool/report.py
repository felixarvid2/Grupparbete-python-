# report.py - gör en läsbar rapport av fynden från auditor.py.
#
# Varje fynd är ett par: (regelnamn, problem)
# t.ex. ("rule_ntp", "No NTP server configured ('ntp server ...')")
# Listan innehåller BARA regler som hittade fel.

from rules import ALL_RULES


def write_line(f, text):
    """Skriver en rad både i terminalen och i rapportfilen."""
    print(text)
    f.write(text + "\n")


def print_report(findings, filename="tests/report.txt"):
    """Skriver rapporten i terminalen och sparar den i en .txt-fil.

    Returnerar antal regler som fick fel (0 = allt var bra).
    """
    failed = 0

    # "w" skriver över filen om den finns; utf-8 gör att å, ä och ö blir rätt
    with open(filename, "w", encoding="utf-8") as f:

        # Går igenom ALLA regler, så att även godkända syns i rapporten
        for rule in ALL_RULES:
            name = rule.__name__

            # Plockar ut de problem som hör till just den här regeln
            problems = []
            for rule_name, problem in findings:
                if rule_name == name:
                    problems.append(problem)

            if problems:
                failed += 1
                write_line(f, f"FEL  {name}")
                for problem in problems:
                    write_line(f, f"       - {problem}")
            else:
                write_line(f, f"OK   {name}")

        total = len(ALL_RULES)
        # \n ger en tom rad före sammanfattningen
        write_line(f, f"\n{total - failed}/{total} regler godkända")

    return failed