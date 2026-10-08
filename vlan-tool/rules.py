import re


# ---------------------------------------------------------------------------
# Hjälpfunktioner
# ---------------------------------------------------------------------------

def is_switch(text):
    """En config med 'switchport'-rader tolkas som en switch, annars router."""
    return "switchport" in text


def get_blocks(lines, keyword):
    """Plockar ut block som börjar med ett nyckelord, t.ex. 'interface'.

    Returnerar en dict: rubrik -> lista med raderna under (utan indrag).
    Exempel: {"interface FastEthernet0/1": ["switchport mode access", ...]}
    """
    blocks = {}
    current = None
    for line in lines:
        if line.startswith(keyword + " "):
            current = line.strip()
            blocks[current] = []
        elif line.startswith(" ") and current:
            blocks[current].append(line.strip())
        else:
            current = None
    return blocks


# ---------------------------------------------------------------------------
# Kärnregler
# ---------------------------------------------------------------------------

def rule_ssh_enabled(lines):
    text = "\n".join(lines)
    problems = []
    if not re.search(r"^ip domain-name \S+", text, re.M):
        problems.append("No domain name set (needed for SSH)")
    if not re.search(r"^ip ssh version 2", text, re.M):
        problems.append("SSH version 2 not set")
    # '$' gör att 'transport input ssh telnet' inte räknas som OK
    if not re.search(r"^\s*transport input ssh\s*$", text, re.M):
        problems.append("SSH not enabled (missing 'transport input ssh')")
    if re.search(r"^\s*transport input .*\b(telnet|all)\b", text, re.M):
        problems.append("Telnet is allowed on vty")
    return problems


def rule_vlans_exist(lines):
    text = "\n".join(lines)
    defined = set(re.findall(r"^vlan (\d+)", text, re.M))
    defined.add("1")  # VLAN 1 finns alltid
    used = set(re.findall(r"switchport access vlan (\d+)", text))
    used |= set(re.findall(r"^interface [Vv]lan ?(\d+)", text, re.M))
    return [f"VLAN {v} is used but not defined" for v in sorted(used - defined)]


def rule_trunk(lines):
    problems = []
    for name, body in get_blocks(lines, "interface").items():
        if "switchport mode trunk" not in body:
            continue
        native = [l for l in body if l.startswith("switchport trunk native vlan")]
        allowed = [l for l in body if l.startswith("switchport trunk allowed vlan")]
        if not native:
            problems.append(f"{name}: trunk has no native VLAN set")
        elif native[0].endswith(" 1"):
            problems.append(f"{name}: native VLAN should not be 1")
        if not allowed:
            problems.append(f"{name}: trunk has no 'allowed vlan' list")
        elif allowed[0].endswith(" all"):
            problems.append(f"{name}: trunk allows all VLANs")
    return problems


# ---------------------------------------------------------------------------
# Extraregler
# ---------------------------------------------------------------------------

def rule_hostname_set(lines):
    if not any(l.startswith("hostname ") for l in lines):
        return ["No hostname configured"]
    return []


def rule_timestamps(lines):
    text = "\n".join(lines)
    problems = []
    for kind in ("debug", "log"):
        if not re.search(rf"^service timestamps {kind} datetime.*msec", text, re.M):
            problems.append(f"'service timestamps {kind} datetime msec' is missing")
    return problems


def rule_logging(lines):
    text = "\n".join(lines)
    problems = []
    if re.search(r"^no logging on", text, re.M):
        problems.append("Logging is turned off ('no logging on')")
    if not re.search(r"^logging (host )?\d+\.\d+\.\d+\.\d+", text, re.M):
        problems.append("No log server configured ('logging host ...')")
    if not re.search(r"^logging buffered", text, re.M):
        problems.append("'logging buffered' is missing")
    return problems


def rule_ntp(lines):
    text = "\n".join(lines)
    if not re.search(r"^ntp server \S+", text, re.M):
        return ["No NTP server configured ('ntp server ...')"]
    return []


def rule_stp_mode(lines):
    text = "\n".join(lines)
    if not is_switch(text):
        return []  # STP gäller bara switchar
    if not re.search(r"^spanning-tree mode rapid-pvst", text, re.M):
        return ["Spanning-tree mode is not rapid-pvst"]
    return []


def rule_nat(lines):
    text = "\n".join(lines)
    if is_switch(text):
        return []  # NAT gäller bara routern
    problems = []
    if not re.search(r"^\s*ip nat inside$", text, re.M):
        problems.append("No interface has 'ip nat inside'")
    if not re.search(r"^\s*ip nat outside$", text, re.M):
        problems.append("No interface has 'ip nat outside'")

    rule = re.search(r"^ip nat inside source list (\S+)", text, re.M)
    if not re.search(r"^ip nat inside source", text, re.M):
        problems.append("No 'ip nat inside source' rule found")
    elif rule:
        acl = re.escape(rule.group(1))
        if not re.search(rf"^(access-list {acl} |ip access-list (standard|extended) {acl}$)", text, re.M):
            problems.append(f"NAT uses ACL {rule.group(1)} which does not exist")
    return problems


# ---------------------------------------------------------------------------
# Regellistor
# ---------------------------------------------------------------------------

CORE_RULES = [rule_ssh_enabled, rule_vlans_exist, rule_trunk]

EXTRA_RULES = [rule_hostname_set, rule_timestamps, rule_logging,
               rule_ntp, rule_stp_mode, rule_nat]

ALL_RULES = CORE_RULES + EXTRA_RULES