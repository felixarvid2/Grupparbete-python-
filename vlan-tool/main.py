# main.py - startpunkten för programmet. Här väljer man VAD som ska hända,
# själva jobbet görs i generator.py, auditor.py och report.py.
#
# Stå i mappen vlan-tool/ och kör:
#   python3 main.py generate              -> skapar konfigfiler i configs/ från CSV-filerna i samples/
#   python3 main.py audit                 -> granskar alla konfigfiler i configs/
#   python3 main.py audit samples/bad.cfg -> granskar bara en fil

import glob
import os
import sys

from generator import read_csv, group_by_switch, generate_switch, generate_router  # bygger konfigarna
from auditor import audit_file                                                     # kör reglerna på en konfig
from report import print_report                                                    # skriver rapporten


#sparar en konfig-text i en fil och skriver ut vilken fil det blev
def save_config(filename, text):
    with open(filename, "w", encoding="utf-8") as f:  # "w" = write, skapar filen eller skriver över den om den redan finns, with stänger filen automatiskt
        f.write(text + "\n")                          # avslutar med en radbrytning 
    print("Sparade", filename)                        # skriver ut i terminalen vilken fil som sparades


#läser alla CSV-filer i samples/ och skapar en konfigfil per switch + en för routern
def generate():
    port_rows = []  # här samlas raderna från ports.csv
    dhcp_rows = []  # här samlas raderna från dhcp.csv

    for path in glob.glob("samples/*.csv"):  # glob hittar alla filer som slutar på .csv i samples/
        file_rows = read_csv(path)           # läs in en CSV-fil i taget

        if len(file_rows) == 0:              # om tom går man vidare till nästa fil
            continue                         

        first_row = file_rows[0]             # kolla vilka kolumner filen har för att veta vad det är för fil
        if "Switch" in first_row:
            port_rows = port_rows + file_rows
        elif "pool_name" in first_row:
            dhcp_rows = dhcp_rows + file_rows

    os.makedirs("configs", exist_ok=True)    # skapar mappen configs/ men om den redan existerar gör den ingenting

    # samlar alla VLAN-namn från alla switchar, t.ex. {"10": "KONTOR", "20": "EKONOMI"}
    # behövs för switchar som bara har trunkar, annars får deras VLAN namn som "VLAN10"
    vlan_names = {}
    for rad in dhcp_rows:
        vlan_names[rad["vlan_id"]] = rad["pool_name"]   # pool-namnet i dhcp.csv är samma som VLAN-namnet
    for rad in port_rows:
        if rad["Vlan_Id"].isdigit():                    # hoppar över trunkrader där Vlan_Id är "Trunk"
            vlan_names[rad["Vlan_Id"]] = rad["Vlan_Namn"]  # namnet i ports.csv går före dhcp.csv

    switches = group_by_switch(port_rows)
    for switch in switches:
        text = generate_switch(switch, switches[switch], vlan_names)
        save_config("configs/" + switch + ".cfg", text)  # en fil per switch

    if len(dhcp_rows) > 0:                   # routern byggs bara om det fanns någon DHCP-fil
        text = generate_router(dhcp_rows)
        save_config("configs/R-Nordvik-1.cfg", text)


#granskar EN konfigfil och sparar rapporten i tests/
def audit_one(path):
    name = os.path.basename(path)            # tar bort mappen: "configs/SW-Nordvik-1.cfg" -> "SW-Nordvik-1.cfg"
    name = name.replace(".cfg", "")          # tar bort ändelsen: "SW-Nordvik-1.cfg" -> "SW-Nordvik-1"

    print()                                  # tom rad så rapporterna inte klistras ihop
    print("=====", path, "=====")
    findings = audit_file(path)              # kör alla regler från rules.py
    print_report(findings, "tests/" + name + "_report.txt")  # t.ex. tests/SW-Nordvik-1_report.txt


#granskar alla konfigfiler i configs/
def audit_all():
    paths = sorted(glob.glob("configs/*.cfg"))  # sorted gör att filerna kommer i bokstavsordning
    if len(paths) == 0:
        print("Hittade inga konfigfiler, kör 'python3 main.py generate' först")
    for path in paths:
        audit_one(path)


# Kör programmet
# sys.argv är en lista med det man skrev i terminalen:
#   plats 0 är filnamnet, plats 1 är kommandot, plats 2 är filen som ska granskas

if len(sys.argv) == 1:                       # bara "main.py", inget kommando skrevs
    command = ""
else:
    command = sys.argv[1]

if command == "generate":
    generate()
elif command == "audit" and len(sys.argv) == 2:   # "audit" utan fil -> granska allt
    audit_all()
elif command == "audit":                          # "audit" med fil -> granska bara den
    audit_one(sys.argv[2])
else:
    print("Fel, du måste skriva något av detta:")
    print("  python3 main.py generate")
    print("  python3 main.py audit")
    print("  python3 main.py audit samples/good or bad.cfg")
