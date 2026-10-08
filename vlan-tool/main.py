import csv

#öppnar csv filen, newline gör att python inte ändrar radbrytningarna encoding="utf.8 gör att den kan läsa åäö, csv.Dictreader läser filen och gör första raden till rubrik"
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

#
def generate_config(rows):
    line = []

vlans = {}
for rad in rows:
    if rad["vlan"]:
        vlans[rad["vlan"]] = rad["vlan_name"]