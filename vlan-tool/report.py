## Sample from Claude

def print_report(results):
    failed = 0
    for name, problems in results:
        if problems:
            failed += 1
            print(f"FAIL  {name}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"PASS  {name}")
    print(f"\n{len(results) - failed}/{len(results)} rules passed")
    return failed