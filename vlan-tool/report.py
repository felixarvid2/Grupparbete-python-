# report.py - gör en läsbar rapport av fynden från auditor.py.
#
# auditor.py ger oss en lista med fynd. Varje fynd är ett par:
#   (regelnamn, problem)
# t.ex. ("rule_ntp", "No NTP server configured ('ntp server ...')")
# Listan innehåller BARA regler som hittade fel.

from rules import ALL_RULES # regler som finns i rules.py


def print_report(findings):
    """Skriver ut en rapport i terminalen med OK eller FEL för varje regel.

    Returnerar antal regler som fick fel (0 = allt var bra).
    """
    failed = 0  # räknar hur många regler som fick fel

    # Gå igenom ALLA regler, så att även godkända regler syns i rapporten
    for rule in ALL_RULES:
        name = rule.__name__

        # Plocka ut de problem som hör till just den här regeln
        problems = []
        for rule_name, problem in findings:
            if rule_name == name:
                problems.append(problem)

        if problems:
            failed += 1
            print(f"FEL  {name}")
            for problem in problems:
                print(f"       - {problem}")
        else:
            print(f"OK   {name}")

    total = len(ALL_RULES)
    print(f"\n{total - failed}/{total} regler godkända")
    return failed