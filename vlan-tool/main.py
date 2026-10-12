import csv
import os

#öppnar csv filen, newline gör att python inte ändrar radbrytningarna encoding="utf.8 gör att den kan läsa åäö, csv.Dictreader läser filen och gör första raden till rubrik"
#lite beroende på hur csv filen ser ut så får man ändra
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

#bygger konfigen för EN switch, rows är bara raderna som hör till den switchen
def generate_config(switch, rows):
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


#delar upp raderna per switch, t.ex. {"SW_Nordvik_1": [rad, rad], "SW_Nordvik_2": [rad, ...]}
def group_by_switch(rows):
    switches = {}
    for rad in rows:
        name = rad["Switch"]
        if name not in switches:
            switches[name] = []  # första gången vi ser switchen, skapa en tom lista
        switches[name].append(rad)
    return switches


# Kör programmet
rows = read_csv("samples/Ports.csv")      # läs in CSV-filen
os.makedirs("configs", exist_ok=True)     # skapar mappen configs/ om den inte redan finns

for switch, switch_rows in group_by_switch(rows).items():
    filename = f"configs/{switch}.cfg"    # en fil per switch, t.ex. configs/SW_Nordvik_1.cfg
    with open(filename, "w", encoding="utf-8") as f:              # "w" = write, skapar filen eller skriver över den om den redan finns, with stänger filen automatiskt
        f.write(generate_config(switch, switch_rows) + "\n")      # bygger konfigen för just den här switchen och skriver den till filen, "\n" avslutar filen med en radbrytning
    print(f"Sparade {filename}")                                  # skriver ut i terminalen vilken fil som sparades
