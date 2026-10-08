# rules.py - regler som granskar en Cisco IOS-config.
#
# Så här fungerar en regel:
#   - Den får en lista med rader (en rad = en textsträng från config-filen).
#   - Den returnerar en lista med felmeddelanden (på engelska).
#   - Tom lista [] betyder att allt är OK.


# ---------------------------------------------------------------------------
# Hjälpfunktioner (används av reglerna längre ner)
# ---------------------------------------------------------------------------

def find_line(lines, start):
    """Letar efter första raden som BÖRJAR med texten 'start'.

    Indraget tas bort först, så " transport input ssh" hittas också.
    Returnerar raden (utan indrag), eller None om ingen rad hittades.
    """
    for line in lines:
        line = line.strip()
        if line.startswith(start):
            return line
    return None


def has_line(lines, start):
    """True om det finns en rad som börjar med 'start', annars False."""
    return find_line(lines, start) is not None


def is_switch(lines):
    """En config med någon 'switchport'-rad tolkas som en switch, annars router."""
    for line in lines:
        if "switchport" in line:
            return True
    return False


def get_blocks(lines, keyword):
    """Plockar ut block som börjar med ett nyckelord, t.ex. 'interface'.

    Ett block är en rubrikrad (utan indrag) följd av rader MED indrag.
    Returnerar en dict: rubrik -> lista med raderna under (utan indrag).
    Exempel: {"interface FastEthernet0/1": ["switchport mode access", ...]}
    """
    blocks = {}
    current = None  # rubriken på blocket vi är inne i just nu

    for line in lines:
        if line.startswith(keyword + " "):
            # Ny rubrik, t.ex. "interface FastEthernet0/1" -> starta ett nytt block
            current = line.strip()
            blocks[current] = []
        elif line.startswith(" ") and current is not None:
            # Rad med indrag -> hör till blocket vi är inne i
            blocks[current].append(line.strip())
        else:
            # Rad utan indrag (t.ex. "!") -> blocket är slut
            current = None

    return blocks


# ---------------------------------------------------------------------------
# Kärnregler (de tre som kursen kräver)
# ---------------------------------------------------------------------------

def rule_ssh_enabled(lines):
    """SSH ska vara aktiverat och telnet ska vara avstängt."""
    problems = []

    # SSH kräver ett domännamn (för att kunna skapa nycklar)
    if not has_line(lines, "ip domain-name "):
        problems.append("No domain name set (needed for SSH)")

    if not has_line(lines, "ip ssh version 2"):
        problems.append("SSH version 2 not set")

    # Vi vill ha EXAKT "transport input ssh". Då räknas inte
    # "transport input ssh telnet" som OK.
    ssh_only = False
    for line in lines:
        if line.strip() == "transport input ssh":
            ssh_only = True
    if not ssh_only:
        problems.append("SSH not enabled (missing 'transport input ssh')")

    # Kolla om någon "transport input"-rad tillåter telnet eller all
    for line in lines:
        line = line.strip()
        if line.startswith("transport input"):
            words = line.split()  # "transport input telnet" -> ["transport", "input", "telnet"]
            if "telnet" in words or "all" in words:
                problems.append("Telnet is allowed on vty")

    return problems


def rule_vlans_exist(lines):
    """Alla VLAN som används ska också vara definierade med 'vlan <nummer>'."""
    # Steg 1: samla VLAN som är definierade
    defined = {"1"}  # VLAN 1 finns alltid
    for line in lines:
        if line.startswith("vlan "):          # t.ex. "vlan 10"
            defined.add(line.split()[1])      # split() ger ["vlan", "10"], vi tar nummer 10

    # Steg 2: samla VLAN som används
    used = set()
    for line in lines:
        line = line.strip()
        if line.startswith("switchport access vlan "):
            used.add(line.split()[-1])        # sista ordet på raden är numret
        if line.lower().startswith("interface vlan"):
            number = line.lower().replace("interface vlan", "").strip()
            if number.isdigit():              # hoppa över t.ex. "interface Vlan" utan nummer
                used.add(number)

    # Steg 3: VLAN som används men inte är definierade är fel
    problems = []
    for vlan in sorted(used - defined, key=int):  # key=int sorterar 2 före 10
        problems.append(f"VLAN {vlan} is used but not defined")
    return problems


def rule_hostname_set(lines):
    """Enheten ska ha ett hostname."""
    if not has_line(lines, "hostname "):
        return ["No hostname configured"]
    return []


# ---------------------------------------------------------------------------
# Extraregler (frivilliga utökningar)
# ---------------------------------------------------------------------------

def rule_trunk(lines):
    """Trunkportar ska ha en native VLAN (inte 1) och en lista med tillåtna VLAN."""
    problems = []

    # Gå igenom alla interface-block, ett i taget
    for name, body in get_blocks(lines, "interface").items():
        if "switchport mode trunk" not in body:
            continue  # inte en trunkport, hoppa till nästa

        native = find_line(body, "switchport trunk native vlan")
        allowed = find_line(body, "switchport trunk allowed vlan")

        if native is None:
            problems.append(f"{name}: trunk has no native VLAN set")
        elif native.split()[-1] == "1":       # sista ordet = VLAN-numret
            problems.append(f"{name}: native VLAN should not be 1")

        if allowed is None:
            problems.append(f"{name}: trunk has no 'allowed vlan' list")
        elif allowed.split()[-1] == "all":
            problems.append(f"{name}: trunk allows all VLANs")

    return problems


def rule_timestamps(lines):
    """Både debug och log ska ha tidsstämplar med millisekunder."""
    problems = []
    for kind in ("debug", "log"):
        line = find_line(lines, f"service timestamps {kind} datetime")
        if line is None or "msec" not in line.split():
            problems.append(f"'service timestamps {kind} datetime msec' is missing")
    return problems


def rule_logging(lines):
    """Loggning ska vara på, ha en loggserver och en buffert."""
    problems = []
    if has_line(lines, "no logging on"):
        problems.append("Logging is turned off ('no logging on')")
    if not has_line(lines, "logging host "):
        problems.append("No log server configured ('logging host ...')")
    if not has_line(lines, "logging buffered"):
        problems.append("'logging buffered' is missing")
    return problems


def rule_ntp(lines):
    """Det ska finnas minst en NTP-server."""
    if not has_line(lines, "ntp server "):
        return ["No NTP server configured ('ntp server ...')"]
    return []


def rule_stp_mode(lines):
    """Switchar ska köra spanning-tree mode rapid-pvst."""
    if not is_switch(lines):
        return []  # STP gäller bara switchar
    if not has_line(lines, "spanning-tree mode rapid-pvst"):
        return ["Spanning-tree mode is not rapid-pvst"]
    return []


def rule_nat(lines):
    """Routern ska ha NAT: inside, outside och en regel som pekar på en ACL."""
    if is_switch(lines):
        return []  # NAT gäller bara routern

    problems = []

    # Kolla att något interface är inside och något outside.
    # Här vill vi ha hela raden exakt, därför == istället för startswith.
    inside = False
    outside = False
    for line in lines:
        if line.strip() == "ip nat inside":
            inside = True
        if line.strip() == "ip nat outside":
            outside = True
    if not inside:
        problems.append("No interface has 'ip nat inside'")
    if not outside:
        problems.append("No interface has 'ip nat outside'")

    # Kolla NAT-regeln, t.ex. "ip nat inside source list 1 interface Gi0/1 overload"
    nat_rule = find_line(lines, "ip nat inside source")
    if nat_rule is None:
        problems.append("No 'ip nat inside source' rule found")
    elif "list" in nat_rule.split():
        words = nat_rule.split()
        acl = words[words.index("list") + 1]  # ordet efter "list" är ACL-namnet/numret

        # Finns ACL:en? Antingen "access-list 1 ..." eller "ip access-list standard NAMN"
        acl_exists = False
        for line in lines:
            if line.startswith(f"access-list {acl} "):
                acl_exists = True
            if line in (f"ip access-list standard {acl}", f"ip access-list extended {acl}"):
                acl_exists = True
        if not acl_exists:
            problems.append(f"NAT uses ACL {acl} which does not exist")

    return problems


# ---------------------------------------------------------------------------
# Regellistor
# ---------------------------------------------------------------------------

CORE_RULES = [rule_ssh_enabled, rule_vlans_exist, rule_hostname_set]

EXTRA_RULES = [rule_trunk, rule_timestamps, rule_logging, rule_ntp, rule_stp_mode, rule_nat]

ALL_RULES = CORE_RULES + EXTRA_RULES