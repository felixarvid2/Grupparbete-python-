import csv

#öppnar csv filen, newline gör att python inte ändrar radbrytningarna encoding="utf.8 gör att den kan läsa åäö, csv.Dictreader läser filen och gör första raden till rubrik"
#lite beroende på hur csv filen ser ut så får man ändra 
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

#
def generate_config(rows):
    lines = []

    vlans = {}
    for rad in rows:
        if rad["vlan"]:
            vlans[rad["vlan"]] = rad["vlan_name"]

    #lägger till vlan nummret och namnet tillexempel 10 KONTOR
    for number, name in vlans.items():
        lines.append(f"vlan {number}")
        lines.append(f" name {name}")

    # 2. Konfigurera varje port
    for rad in rows:
        lines.append(f"interface {rad['interface']}")  # vilken port som konfigureras
        if rad["mode"] == "access":  # bara för access-portar
            lines.append(" switchport mode access")                 # gör porten till access-port
            lines.append(f" switchport access vlan {rad['vlan']}")  # placerar porten i rätt VLAN
        elif rad["mode"] == "trunk":
            lines.append(" switchport mode trunk")
            allowed = rad["allowed_vlans"].replace(";", ",")
            lines.append(f" switchport trunk allowed vlan {allowed}")
