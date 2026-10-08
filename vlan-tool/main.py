import csv


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def generate_config(rows):
    line = []

vlans = {}
for r i rows:
    if r["vlan"]:
        vlans[r["vlan"]] = r["vlan_name"]