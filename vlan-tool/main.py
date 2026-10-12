import glob
import os

from generator import read_csv, group_by_switch, generate_switch  # själva konfig-byggandet finns i generator.py


# Kör programmet
rows = []
for path in glob.glob("samples/*.csv"):  # glob hittar alla filer som slutar på .csv i samples/
    file_rows = read_csv(path)           # läs in en CSV-fil i taget
    if not file_rows or "Switch" not in file_rows[0]:  # hoppa över tomma filer och filer utan Switch-kolumn, t.ex. dhcp.csv
        print(f"Hoppar över {path}")
        continue                         # continue = gå direkt till nästa fil
    rows += file_rows                    # lägger till raderna i den gemensamma listan, så samma switch i flera filer hamnar i samma konfig

os.makedirs("configs", exist_ok=True)     # skapar mappen configs/ om den inte redan finns

for switch, switch_rows in group_by_switch(rows).items():
    filename = f"configs/{switch}.cfg"    # en fil per switch, t.ex. configs/SW-Nordvik-1.cfg
    with open(filename, "w", encoding="utf-8") as f:              # "w" = write, skapar filen eller skriver över den om den redan finns, with stänger filen automatiskt
        f.write(generate_switch(switch, switch_rows) + "\n")      # bygger konfigen för just den här switchen och skriver den till filen, "\n" avslutar filen med en radbrytning
    print(f"Sparade {filename}")                                  # skriver ut i terminalen vilken fil som sparades
