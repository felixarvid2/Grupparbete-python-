# generator.py - läser CSV-filer och bygger Cisco IOS-konfig som text.
#
# Switchar byggs från ports.csv, routern byggs från dhcp.csv.
# Själva sparandet till filer görs i main.py.

import csv

# Inställningar som är samma för alla enheter, ändra här istället för inne i koden
DOMAIN = "nordvik.example"
LOG_SERVER = "192.168.1.17"
NTP_SERVER = "192.168.1.16"
WAN_IP = "203.0.113.10 255.255.255.0"  # routerns port mot operatören
WAN_GATEWAY = "203.0.113.1"


#öppnar csv filen, newline gör att python inte ändrar radbrytningarna, encoding="utf-8" gör att den kan läsa åäö
#csv.DictReader gör första raden till rubrik, strip() tar bort mellanslag som Excel ibland lägger till
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k.strip(): (v or "").strip() for k, v in rad.items()} for rad in csv.DictReader(f)]


#delar upp raderna per switch, t.ex. {"SW-Nordvik-1": [rad, rad], "SW-Nordvik-2": [rad, ...]}
def group_by_switch(rows):
    switches = {}
    for rad in rows:
        switches.setdefault(rad["Switch"], []).append(rad)  # skapar en tom lista första gången
    return switches

#gör om "10;20;99" eller "10,20,99" till ["10", "20", "99"]
def split_vlans(text):
    return [v.strip() for v in text.replace(";", ",").split(",") if v.strip().isdigit()]

#raderna som ALLA enheter ska ha (tidsstämplar, SSH, loggning, NTP)
def base_config(hostname):
    return [
        "!",
        "service timestamps debug datetime msec",
        "service timestamps log datetime msec",
        "!",
        f"hostname {hostname}",
        "!",
        "no ip domain-lookup",
        f"ip domain-name {DOMAIN}",
        "ip ssh version 2",
        "!",
        "username drift secret CHANGE_ME",
        "!",
    ]

#raderna som ALLA enheter ska ha i slutet
def end_config():
    return [
        f"logging buffered 16384",
        f"logging host {LOG_SERVER}",
        f"ntp server {NTP_SERVER}",
        "!",
        "line con 0",
        " logging synchronous",
        "line vty 0 4",
        " transport input ssh",  # bara SSH, inte telnet
        " login local",
        "!",
        "end",
    ]



#bygger konfigen för EN switch, rows är bara raderna som hör till den switchen
#vlan_names är t.ex. {"10": "KONTOR"} och används för VLAN som bara finns på trunkar
def generate_switch(switch, rows, vlan_names=None):
    vlan_names = vlan_names or {}
    lines = base_config(switch)
    #transparent gör att VLAN-definitionerna hamnar i running-config istället för bara vlan.dat
    lines += ["vtp mode transparent", "spanning-tree mode rapid-pvst", "!"]


 #samla alla VLAN switchen behöver: access-VLAN, VLAN som går på trunken och native-VLAN
    vlans = {}
    for rad in rows:
        if rad["Vlan_Id"].isdigit():
            vlans[rad["Vlan_Id"]] = rad["Vlan_Namn"]
        for v in split_vlans(rad["Tillatna_Vlan"]):
            vlans.setdefault(v, vlan_names.get(v, f"VLAN{v}"))
        if rad["Native_Vlan"].isdigit():
            vlans.setdefault(rad["Native_Vlan"], "NATIVE")


    #lägger till vlan nummret och namnet, sorterat så 10 kommer före 99
    for number in sorted(vlans, key=int):
        lines.append(f"vlan {number}")
        lines.append(f" name {vlans[number]}")
    lines.append("!")

    for rad in rows:
        lines.append(f"interface {rad['Port']}")
        if rad["Beskrivning"]:
            lines.append(f" description {rad['Beskrivning']}")

        mode = rad["Lage"].lower()  # "Access" och "access" ska räknas lika
        if mode == "access":
            lines.append(" switchport mode access")
            lines.append(f" switchport access vlan {rad['Vlan_Id']}")
            lines.append(" spanning-tree portfast")         # porten går upp direkt, bara mot datorer
            lines.append(" spanning-tree bpduguard enable") # stänger porten om någon kopplar in en switch
        elif mode == "trunk":
            lines.append(" switchport mode trunk")
            lines.append(f" switchport trunk native vlan {rad['Native_Vlan']}")
            lines.append(f" switchport trunk allowed vlan {','.join(split_vlans(rad['Tillatna_Vlan']))}")
        else:
            raise ValueError(f"{switch} {rad['Port']}: okänt läge '{rad['Lage']}', ska vara access eller trunk")

        #Status "Down" i CSV:n = porten stängs av, allt annat = porten är på
        lines.append(" shutdown" if rad["Status"].lower() == "down" else " no shutdown")
        lines.append("!")

    return "\n".join(lines + end_config())



#bygger routerns konfig, en rad i dhcp.csv = ett VLAN med subinterface och DHCP-pool
def generate_router(dhcp_rows, hostname="R-Nordvik-1", native_vlan="999"):
    lines = base_config(hostname)

    #adresser som inte delas ut till datorer (routern, skrivare, servrar...)
    for d in dhcp_rows:
        lines.append(f"ip dhcp excluded-address {d['excluded_start']} {d['excluded_end']}")
    lines.append("!")

    #en DHCP-pool per VLAN
    for d in dhcp_rows:
        lines += [
            f"ip dhcp pool {d['pool_name']}",
            f" network {d['network']} {d['mask']}",
            f" default-router {d['gateway']}",
            f" dns-server {d['dns']}",
        ]
    lines.append("!")

    #själva porten mot switchen måste slås på, annars kommer inga subinterface upp
    lines += [
        "interface GigabitEthernet0/0",
        " description Trunk mot SW-Nordvik-1",
        " no ip address",
        " no shutdown",
        "!",
    ]

    #ett subinterface per VLAN, gatewayen i CSV:n blir routerns adress i det VLAN:et
    for d in dhcp_rows:
        lines += [
            f"interface GigabitEthernet0/0.{d['vlan_id']}",
            f" description {d['pool_name']}",
            f" encapsulation dot1Q {d['vlan_id']}",
            f" ip address {d['gateway']} {d['mask']}",
            " ip nat inside",
            "!",
        ]

    #native-VLAN måste matcha switcharnas trunkar
    lines += [
        f"interface GigabitEthernet0/0.{native_vlan}",
        " description NATIVE",
        f" encapsulation dot1Q {native_vlan} native",
        "!",
    ]

    #porten mot internet + NAT så att alla VLAN kan dela på routerns publika adress
    lines += [
        "interface GigabitEthernet0/1",
        " description Uplink mot Operator",
        f" ip address {WAN_IP}",
        " ip nat outside",
        " no shutdown",
        "!",
        "ip nat inside source list 1 interface GigabitEthernet0/1 overload",
        "access-list 1 permit 192.168.1.0 0.0.0.255",
        f"ip route 0.0.0.0 0.0.0.0 {WAN_GATEWAY}",
        "!",
    ]

    return "\n".join(lines + end_config())

