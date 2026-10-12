# generator.py - läser CSV-filer och bygger Cisco IOS-konfig som text.
#
# Switchar byggs från ports.csv, routern byggs från dhcp.csv.
# Själva sparandet till filer görs i main.py.

import csv

#öppnar csv filen, newline gör att python inte ändrar radbrytningarna encoding="utf.8 gör att den kan läsa åäö, csv.Dictreader läser filen och gör första raden till rubrik"
#lite beroende på hur csv filen ser ut så får man ändra
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


#delar upp raderna per switch, t.ex. {"SW-Nordvik-1": [rad, rad], "SW-Nordvik-2": [rad, ...]}
def group_by_switch(rows):
    switches = {}
    for rad in rows:
        name = rad["Switch"]
        if name not in switches:
            switches[name] = []  # första gången vi ser switchen, skapa en tom lista
        switches[name].append(rad)
    return switches


#bygger konfigen för EN switch, rows är bara raderna som hör till den switchen
def generate_switch(switch, rows):
    lines = [f"hostname {switch}"]  # varje fil får switchens namn som hostname

    vlans = {}
    for rad in rows:
        if rad["Vlan_Id"].isdigit():  # bara riktiga VLAN-nummer, hoppar över t.ex. "Trunk" eller tom ruta
            vlans[rad["Vlan_Id"]] = rad["Vlan_Namn"]

    #lägger till vlan nummret och namnet tillexempel 10 KONTOR
    for number, name in vlans.items():
        lines.append(f"vlan {number}")
        lines.append(f" name {name}")

    for rad in rows:
        lines.append(f"interface {rad['Port']}")  # vilken port som konfigureras
        mode = rad["Lage"].lower()  # lower() gör "Access" till "access" så stora/små bokstäver inte spelar roll
        if mode == "access":  # bara för access-portar
            lines.append(" switchport mode access")                    # gör porten till access-port
            lines.append(f" switchport access vlan {rad['Vlan_Id']}")  # placerar porten i rätt VLAN
        elif mode == "trunk":  # elif = "annars om", kollas bara om porten INTE var access, en port kan bara ha ett läge så båda kan aldrig köras
            lines.append(" switchport mode trunk") # gör porten till trunkport
            allowed = rad["Tillatna_Vlan"].replace(";", ",") # byter 10;20;99 till 10,20,99
            lines.append(f" switchport trunk allowed vlan {allowed}") # vilka VLAN som får gå över trunken
    return "\n".join(lines)  # slår ihop listan till en text, en rad per kommando


#bygger routerns konfig, en rad i dhcp.csv = ett VLAN med subinterface och DHCP-pool
def generate_router(dhcp_rows):
    lines = ["hostname R-Nordvik-1", "!"]

    #ett subinterface per VLAN, gatewayen i CSV:n blir routerns adress i det VLAN:et
    for d in dhcp_rows:
        lines += [
            f"interface Gi0/0.{d['vlan_id']}",
            f" encapsulation dot1Q {d['vlan_id']}",
            f" ip address {d['gateway']} {d['mask']}",
            "!",
        ]

    #en DHCP-pool per VLAN, excluded-address är adresser som inte delas ut till datorer
    for d in dhcp_rows:
        lines += [
            f"ip dhcp excluded-address {d['excluded_start']} {d['excluded_end']}",
            f"ip dhcp pool {d['pool_name']}",
            f" network {d['network']} {d['mask']}",
            f" default-router {d['gateway']}",
            f" dns-server {d['dns']}",
            "!",
        ]
    return "\n".join(lines)
