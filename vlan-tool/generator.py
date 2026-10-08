## sample from Claude

import csv, ipaddress

def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def generate_switch(vlans):
    out = ["hostname SW-Nordvik-1", "!"]
    for v in vlans:
        out += [f"vlan {v['vlan_id']}", f" name {v['name']}", "!"]
    out += ["line vty 0 4", " transport input ssh", "!", "ip ssh version 2"]
    return out

def generate_router(vlans, dhcp):
    out = ["hostname R-Nordvik-1", "!"]
    for v in vlans:
        net = ipaddress.ip_network(f"{v['network']}/{v['mask']}")
        gateway = next(net.hosts())  # assumption: first usable address
        out += [
            f"interface Gi0/0.{v['vlan_id']}",
            f" encapsulation dot1Q {v['vlan_id']}",
            f" ip address {gateway} {v['mask']}",
            "!",
        ]
    for d in dhcp:
        out += [
            f"ip dhcp excluded-address {d['excluded_start']} {d['excluded_end']}",
            f"ip dhcp pool {d['pool_name']}",
            f" network {d['network']} {d['mask']}",
            f" default-router {d['gateway']}",
            "!",
        ]
    return out