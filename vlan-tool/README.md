Kända begränsningar i nuvarande program:

Måste göras för hand på varje enhet

crypto key generate rsa hamnar inte i konfigfilen. Utan nycklarna fungerar inte SSH, trots att configen ser rätt ut.

Syns inte i running-config, så granskaren kan inte kontrollera det

Packet Tracer visar inte logging buffered, så den raden granskas inte (rule_logging är borttagen). Raden skrivs ändå i genererade configar.
Loggservern visas som logging <adress> utan host, och granskaren kan därför inte kontrollera den heller.