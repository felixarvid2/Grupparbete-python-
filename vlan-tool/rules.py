# rules.py - regler som granskar en Cisco IOS-config.
#
# Så här fungerar en regel:
#   - Den får en lista med rader (en rad = en textsträng från config-filen).
#   - Den returnerar en lista med felmeddelanden (på engelska).
#   - Tom lista [] betyder att allt är OK.


# ---------------------------------------------------------------------------
# Hjälpfunktioner (används av reglerna längre ner)
# ---------------------------------------------------------------------------

# Hjälpfunktion: hittar första raden som börjar med en viss text
def find_line(lines, start):
    """Letar efter första raden som BÖRJAR med texten 'start'.

    Indraget tas bort först, så " transport input ssh" hittas också.
    Returnerar raden (utan indrag), eller None om ingen rad hittades.
    """
    # Går igenom config-raderna en i taget
    for line in lines:
        # Tar bort mellanslag i början och slutet av raden (indraget)
        line = line.strip()
        # Kollar om raden börjar med texten vi letar efter
        if line.startswith(start):
            # Hittad: lämnar tillbaka raden och avslutar funktionen direkt
            return line
    # Ingen rad matchade: lämnar tillbaka None (betyder "ingenting")
    return None


# Hjälpfunktion: svarar bara ja/nej på om en rad finns
def has_line(lines, start):
    """True om det finns en rad som börjar med 'start', annars False."""
    # Använder find_line: hittar den en rad blir svaret True, annars False
    return find_line(lines, start) is not None


# Hjälpfunktion: avgör om configen kommer från en switch eller en router
def is_switch(lines):
    """En config med någon 'switchport'-rad tolkas som en switch, annars router."""
    # Går igenom alla rader
    for line in lines:
        # Innehåller raden ordet "switchport" är det en switch
        if "switchport" in line:
            # Switch hittad, svara True direkt
            return True
    # Ingen switchport-rad hittades, alltså tolkas den som en router
    return False


# Hjälpfunktion: delar upp configen i block (t.ex. ett block per interface)
def get_blocks(lines, keyword):
    """Plockar ut block som börjar med ett nyckelord, t.ex. 'interface'.

    Ett block är en rubrikrad (utan indrag) följd av rader MED indrag.
    Returnerar en dict: rubrik -> lista med raderna under (utan indrag).
    Exempel: {"interface FastEthernet0/1": ["switchport mode access", ...]}
    """
    # Tom dict (ordlista) som fylls på: rubrik -> lista med rader
    blocks = {}
    # Håller reda på vilket block vi är i just nu (None = inget block)
    current = None  # rubriken på blocket vi är inne i just nu

    # Går igenom alla rader i configen
    for line in lines:
        # Börjar raden med t.ex. "interface " är det en ny rubrik
        if line.startswith(keyword + " "):
            # Ny rubrik, t.ex. "interface FastEthernet0/1" -> starta ett nytt block
            # Sparar rubriken (utan mellanslag runt) som nuvarande block
            current = line.strip()
            # Skapar en tom lista för raderna som kommer att höra till blocket
            blocks[current] = []
        # Börjar raden med mellanslag (indrag) och vi är i ett block?
        elif line.startswith(" ") and current is not None:
            # Rad med indrag -> hör till blocket vi är inne i
            # Lägger raden (utan indrag) i listan för nuvarande block
            blocks[current].append(line.strip())
        # Alla andra rader, t.ex. "!" eller en ny rad utan indrag
        else:
            # Rad utan indrag (t.ex. "!") -> blocket är slut
            # Nollställer så att vi inte längre räknas vara i ett block
            current = None

    # Lämnar tillbaka alla block vi hittade
    return blocks


# ---------------------------------------------------------------------------
# Kärnregler (de tre som kursen kräver)
# ---------------------------------------------------------------------------

# Regel: SSH ska vara på och telnet av
def rule_ssh_enabled(lines):
    """SSH ska vara aktiverat och telnet ska vara avstängt."""
    # Lista där vi samlar felmeddelanden (förblir tom om allt är OK)
    problems = []

    # SSH kräver ett domännamn (för att kunna skapa nycklar)
    # Finns ingen rad som börjar med "ip domain-name " saknas domännamnet
    if not has_line(lines, "ip domain-name "):
        # Lägger till felmeddelandet i listan
        problems.append("No domain name set (needed for SSH)")

    # Finns ingen rad "ip ssh version 2" är SSH version 2 inte påslaget
    if not has_line(lines, "ip ssh version 2"):
        # Lägger till felmeddelandet i listan
        problems.append("SSH version 2 not set")

    # Vi vill ha EXAKT "transport input ssh". Då räknas inte
    # "transport input ssh telnet" som OK.
    # Flagga som säger om vi har hittat raden än (börjar som False)
    ssh_only = False
    # Går igenom alla rader
    for line in lines:
        # Jämför hela raden (utan indrag) med exakt "transport input ssh"
        if line.strip() == "transport input ssh":
            # Raden fanns, så vi sätter flaggan till True
            ssh_only = True
    # Är flaggan fortfarande False fanns raden inte
    if not ssh_only:
        # Lägger till felmeddelandet i listan
        problems.append("SSH not enabled (missing 'transport input ssh')")

    # Kolla om någon "transport input"-rad tillåter telnet eller all
    # Går igenom alla rader igen
    for line in lines:
        # Tar bort indraget så startswith fungerar
        line = line.strip()
        # Är det en "transport input"-rad?
        if line.startswith("transport input"):
            words = line.split()  # "transport input telnet" -> ["transport", "input", "telnet"]
            # Står "telnet" eller "all" bland orden på raden är telnet tillåtet
            if "telnet" in words or "all" in words:
                # Lägger till felmeddelandet i listan
                problems.append("Telnet is allowed on vty")

    # Lämnar tillbaka alla fel (tom lista om allt var OK)
    return problems


# Regel: alla VLAN som används ska vara definierade
def rule_vlans_exist(lines):
    """Alla VLAN som används ska också vara definierade med 'vlan <nummer>'."""
    # Steg 1: samla VLAN som är definierade
    # Mängd (set) med definierade VLAN, startar med "1" som alltid finns
    defined = {"1"}  # VLAN 1 finns alltid
    # Går igenom alla rader
    for line in lines:
        # Börjar raden med "vlan " är det en VLAN-definition
        if line.startswith("vlan "):          # t.ex. "vlan 10"
            # Delar raden i ord och lägger till numret (ord nummer 2) i mängden
            defined.add(line.split()[1])      # split() ger ["vlan", "10"], vi tar nummer 10

    # Steg 2: samla VLAN som används
    # Tom mängd som fylls med VLAN-nummer som används någonstans
    used = set()
    # Går igenom alla rader
    for line in lines:
        # Tar bort indraget
        line = line.strip()
        # Är det en rad som sätter VLAN på en accessport?
        if line.startswith("switchport access vlan "):
            # Lägger till sista ordet (VLAN-numret) i mängden
            used.add(line.split()[-1])        # sista ordet på raden är numret
        # Gör raden till små bokstäver och kollar om det är t.ex. "interface Vlan99"
        if line.lower().startswith("interface vlan"):
            # Tar bort texten "interface vlan" så bara numret blir kvar
            number = line.lower().replace("interface vlan", "").strip()
            # Bara om det som blev kvar är siffror är det ett VLAN-nummer
            if number.isdigit():              # hoppa över t.ex. "interface Vlan" utan nummer
                # Lägger till numret i mängden
                used.add(number)

    # Steg 3: VLAN som används men inte är definierade är fel
    # Lista för felmeddelanden
    problems = []
    # used - defined = VLAN som används men saknas; sorteras som tal, inte text
    for vlan in sorted(used - defined, key=int):  # key=int sorterar 2 före 10
        # Lägger till ett felmeddelande för varje saknat VLAN
        problems.append(f"VLAN {vlan} is used but not defined")
    # Lämnar tillbaka felen
    return problems


# Regel: enheten ska ha ett hostname
def rule_hostname_set(lines):
    """Enheten ska ha ett hostname."""
    # Finns ingen rad som börjar med "hostname " saknas det
    if not has_line(lines, "hostname "):
        # Lämnar tillbaka en lista med ett felmeddelande
        return ["No hostname configured"]
    # Annars är allt OK: tom lista
    return []


# ---------------------------------------------------------------------------
# Extraregler (frivilliga utökningar)
# ---------------------------------------------------------------------------

# Regel: trunkportar ska ha native VLAN och en lista med tillåtna VLAN
def rule_trunk(lines):
    """Trunkportar ska ha en native VLAN (inte 1) och en lista med tillåtna VLAN."""
    # Lista för felmeddelanden
    problems = []

    # Gå igenom alla interface-block, ett i taget
    # items() ger par av (rubrik, rader under rubriken)
    for name, body in get_blocks(lines, "interface").items():
        # Är interfacet inte i trunk-läge?
        if "switchport mode trunk" not in body:
            # Hoppa över det och gå till nästa interface
            continue  # inte en trunkport, hoppa till nästa

        # Letar upp raden med native VLAN i interfacets rader (eller None)
        native = find_line(body, "switchport trunk native vlan")
        # Letar upp raden med tillåtna VLAN i interfacets rader (eller None)
        allowed = find_line(body, "switchport trunk allowed vlan")

        # Saknas raden helt?
        if native is None:
            # Lägger till felmeddelande med interfacets namn
            problems.append(f"{name}: trunk has no native VLAN set")
        # Finns raden men det sista ordet (VLAN-numret) är 1?
        elif native.split()[-1] == "1":       # sista ordet = VLAN-numret
            # Lägger till felmeddelande
            problems.append(f"{name}: native VLAN should not be 1")

        # Saknas listan med tillåtna VLAN?
        if allowed is None:
            # Lägger till felmeddelande
            problems.append(f"{name}: trunk has no 'allowed vlan' list")
        # Finns den men sista ordet är "all" (alla VLAN släpps igenom)?
        elif allowed.split()[-1] == "all":
            # Lägger till felmeddelande
            problems.append(f"{name}: trunk allows all VLANs")

    # Lämnar tillbaka alla fel
    return problems


# Regel: tidsstämplar med millisekunder
def rule_timestamps(lines):
    """Både debug och log ska ha tidsstämplar med millisekunder."""
    # Lista för felmeddelanden
    problems = []
    # Kontrollerar två sorter: debug och log
    for kind in ("debug", "log"):
        # Letar efter t.ex. "service timestamps debug datetime..." (eller None)
        line = find_line(lines, f"service timestamps {kind} datetime")
        # Fel om raden saknas, eller om ordet "msec" inte finns bland orden på raden
        if line is None or "msec" not in line.split():
            # Lägger till felmeddelande (kind blir "debug" eller "log")
            problems.append(f"'service timestamps {kind} datetime msec' is missing")
    # Lämnar tillbaka alla fel
    return problems


# Regel: loggning ska vara på med loggserver och buffert
def rule_logging(lines):
    """Loggning ska vara på, ha en loggserver och en buffert."""
    # Lista för felmeddelanden
    problems = []
    # Finns raden "no logging on" är loggningen avstängd
    if has_line(lines, "no logging on"):
        # Lägger till felmeddelande
        problems.append("Logging is turned off ('no logging on')")
    # Loggservern kan stå som "logging host 1.2.3.4" eller bara "logging 1.2.3.4"
    # (Packet Tracer skriver den korta formen)
    # Flagga som blir True om vi hittar en loggserver
    has_server = False
    # Går igenom alla rader
    for line in lines:
        # Delar raden i ord, t.ex. "logging 192.168.1.17" -> ["logging", "192.168.1.17"]
        words = line.split()
        # Raden ska ha minst två ord och börja med "logging"
        if len(words) >= 2 and words[0] == "logging":
            # Andra ordet är antingen "host" eller en IP-adress (börjar med en siffra)
            if words[1] == "host" or words[1][0].isdigit():
                # Då finns en loggserver
                has_server = True
    # Hittades ingen loggserver?
    if not has_server:
        # Lägger till felmeddelande
        problems.append("No log server configured ('logging host ...')")
    # Finns ingen rad "logging buffered..." saknas bufferten
    if not has_line(lines, "logging buffered"):
        # Lägger till felmeddelande
        problems.append("'logging buffered' is missing")
    # Lämnar tillbaka alla fel
    return problems


# Regel: det ska finnas en NTP-server
def rule_ntp(lines):
    """Det ska finnas minst en NTP-server."""
    # Finns ingen rad som börjar med "ntp server " saknas NTP-server
    if not has_line(lines, "ntp server "):
        # Lämnar tillbaka en lista med ett felmeddelande
        return ["No NTP server configured ('ntp server ...')"]
    # Annars är allt OK: tom lista
    return []


# Regel: switchar ska köra rapid-pvst
def rule_stp_mode(lines):
    """Switchar ska köra spanning-tree mode rapid-pvst."""
    # Är det inte en switch (alltså en router)?
    if not is_switch(lines):
        # Regeln gäller inte routern, så vi lämnar tillbaka tom lista
        return []  # STP gäller bara switchar
    # Finns ingen rad "spanning-tree mode rapid-pvst"?
    if not has_line(lines, "spanning-tree mode rapid-pvst"):
        # Lämnar tillbaka en lista med ett felmeddelande
        return ["Spanning-tree mode is not rapid-pvst"]
    # Annars är allt OK: tom lista
    return []


# Regel: routern ska ha fungerande NAT (inside, outside, NAT-regel)
def rule_nat(lines):
    """Routern ska ha NAT: inside, outside och en regel som pekar på en ACL
    och på outside-interfacet (porten mot operatören)."""
    # Är det en switch?
    if is_switch(lines):
        # Regeln gäller inte switchen, så vi lämnar tillbaka tom lista
        return []  # NAT gäller bara routern

    # Lista för felmeddelanden
    problems = []

    # Kolla att något interface är inside och något outside.
    # Här vill vi ha hela raden exakt, därför == istället för startswith.
    # Flaggor som blir True när vi hittar respektive rad
    inside = False
    outside = False
    # Går igenom alla rader
    for line in lines:
        # Är raden exakt "ip nat inside"?
        if line.strip() == "ip nat inside":
            # Då har minst ett interface inside-NAT
            inside = True
        # Är raden exakt "ip nat outside"?
        if line.strip() == "ip nat outside":
            # Då har minst ett interface outside-NAT
            outside = True
    # Hittades ingen inside-rad?
    if not inside:
        # Lägger till felmeddelande
        problems.append("No interface has 'ip nat inside'")
    # Hittades ingen outside-rad?
    if not outside:
        # Lägger till felmeddelande
        problems.append("No interface has 'ip nat outside'")

    # Kolla NAT-regeln, t.ex. "ip nat inside source list 1 interface Gi0/1 overload"
    # Letar upp NAT-regeln (eller None om den saknas)
    nat_rule = find_line(lines, "ip nat inside source")
    # Finns ingen NAT-regel?
    if nat_rule is None:
        # Lägger till felmeddelande
        problems.append("No 'ip nat inside source' rule found")
    # Annars: NAT-regeln finns och vi kontrollerar vad den pekar på
    else:
        # Delar NAT-regeln i ord, t.ex. ["ip", "nat", "inside", "source", "list", "1", ...]
        words = nat_rule.split()

        # Använder regeln en ACL ("list <namn>")? Då måste ACL:en finnas.
        if "list" in words:
            # Plockar ut ACL-numret/namnet: ordet direkt efter "list"
            acl = words[words.index("list") + 1]  # ordet efter "list" är ACL-namnet/numret

            # Finns ACL:en? Antingen "access-list 1 ..." eller "ip access-list standard NAMN"
            # Flagga som blir True om vi hittar ACL:en
            acl_exists = False
            # Går igenom alla rader
            for line in lines:
                # Börjar raden med "access-list <numret> "?
                if line.startswith(f"access-list {acl} "):
                    # Då finns ACL:en
                    acl_exists = True
                # Är raden en namngiven ACL (standard eller extended) med rätt namn?
                if line in (f"ip access-list standard {acl}", f"ip access-list extended {acl}"):
                    # Då finns ACL:en
                    acl_exists = True
            # Hittades ingen ACL?
            if not acl_exists:
                # Lägger till felmeddelande
                problems.append(f"NAT uses ACL {acl} which does not exist")

        # Pekar regeln på ett interface ("interface <namn>")? Då ska det vara
        # porten mot operatören, alltså ha 'ip nat outside'.
        if "interface" in words:
            # Plockar ut interfacets namn: ordet direkt efter "interface"
            out_name = words[words.index("interface") + 1]  # ordet efter "interface"
            # Hämtar alla interface-block i configen
            blocks = get_blocks(lines, "interface")
            # Finns inget interface med det namnet?
            if "interface " + out_name not in blocks:
                # Lägger till felmeddelande
                problems.append(f"NAT points to {out_name} which does not exist")
            # Finns interfacet men saknar det "ip nat outside"?
            elif "ip nat outside" not in blocks["interface " + out_name]:
                # Lägger till felmeddelande
                problems.append(f"NAT points to {out_name} which is not 'ip nat outside'")

    # Lämnar tillbaka alla fel
    return problems


# ---------------------------------------------------------------------------
# Regellistor
# ---------------------------------------------------------------------------

# De tre kärnreglerna (funktionerna läggs i en lista, utan parenteser = de körs inte än)
CORE_RULES = [rule_ssh_enabled, rule_vlans_exist, rule_hostname_set]

# Extrareglerna (frivilliga utökningar)
EXTRA_RULES = [rule_trunk, rule_timestamps, rule_logging, rule_ntp, rule_stp_mode, rule_nat]

# Alla regler i en lista; auditor.py och report.py loopar över den här
ALL_RULES = CORE_RULES + EXTRA_RULES