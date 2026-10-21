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
    return None  # None betyder "ingenting"


def has_line(lines, start):
    """True om det finns en rad som börjar med 'start', annars False."""
    return find_line(lines, start) is not None


def get_blocks(lines, keyword):
    """Plockar ut block som börjar med ett nyckelord, t.ex. 'interface'.

    Ett block är en rubrikrad (utan indrag) följd av rader MED indrag.
    Returnerar en dict: rubrik -> lista med raderna under (utan indrag).
    Exempel: {"interface FastEthernet0/1": ["switchport mode access", ...]}
    """
    blocks = {}
    current = None  # rubriken på blocket vi är inne i (None = inget block)

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

    # Vi vill ha EXAKT "transport input ssh", så "transport input ssh telnet"
    # räknas inte som OK.
    ssh_only = False
    for line in lines:
        if line.strip() == "transport input ssh":
            ssh_only = True
    if not ssh_only:
        problems.append("SSH not enabled (missing 'transport input ssh')")

    # Kollar om någon "transport input"-rad tillåter telnet eller all
    for line in lines:
        line = line.strip()
        if line.startswith("transport input"):
            words = line.split()  # "transport input telnet" -> ["transport", "input", "telnet"]
            if "telnet" in words or "all" in words:
                problems.append("Telnet is allowed on vty")

    return problems


def rule_vlans_exist(lines):
    """Alla VLAN som används ska också vara definierade med 'vlan <nummer>'."""
    # Steg 1: samla VLAN som är definierade (set = mängd utan dubbletter)
    defined = {"1"}  # VLAN 1 finns alltid
    for line in lines:
        if line.startswith("vlan "):          # t.ex. "vlan 10"
            defined.add(line.split()[1])      # split() ger ["vlan", "10"], vi tar numret

    # Steg 2: samla VLAN som används
    used = set()
    for line in lines:
        line = line.strip()
        if line.startswith("switchport access vlan "):
            used.add(line.split()[-1])        # sista ordet på raden är numret
        # Hanteringsinterfacet, t.ex. "interface Vlan99"
        if line.lower().startswith("interface vlan"):
            number = line.lower().replace("interface vlan", "").strip()
            if number.isdigit():              # hoppar över t.ex. "interface Vlan" utan nummer
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
# Extraregel (frivillig utökning)
# ---------------------------------------------------------------------------

def rule_trunk(lines):
    """Trunkportar ska ha en native VLAN (inte 1) och en lista med tillåtna VLAN."""
    problems = []

    # items() ger par av (rubrik, rader under rubriken)
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
        elif allowed.split()[-1] == "all":    # alla VLAN släpps igenom
            problems.append(f"{name}: trunk allows all VLANs")

    return problems


# ---------------------------------------------------------------------------
# Regellistor
# ---------------------------------------------------------------------------

# Funktionerna läggs i listor utan parenteser, alltså körs de inte än
CORE_RULES = [rule_ssh_enabled, rule_vlans_exist, rule_hostname_set]
EXTRA_RULES = [rule_trunk]

# auditor.py och report.py loopar över den här
ALL_RULES = CORE_RULES + EXTRA_RULES