# Projekt_Kontener

Projekt_Kontener to lekki silnik konteneryzacji napisany od zera. Projekt został stworzony w celach edukacyjnych, aby zrozumieć mechanizmy izolacji procesów w jądrze Linuxa oraz zaprezentować dobre praktyki z zakresu automatyzacji infrastruktury (Infrastructure as Code).

---

## Cel projektu

Zamiast korzystać z gotowych rozwiązań takich jak Docker, stworzyliśmy własny skrypt, który od podstaw buduje wyizolowane środowisko uruchomieniowe dla procesów. Uruchomiony w ten sposób kontener "uznaje", że jest niezależnym systemem operacyjnym – posiada własną przestrzeń sieciową, odizolowany system plików oraz nałożone limity zasobów sprzętowych.

## Wykorzystane mechanizmy

Projekt demonstruje w praktyce zastosowanie kluczowych mechanizmów izolacyjnych jądra Linux:

### Mechanizm Podwójnego Rozwidlenia (Double Fork):

Aby poprawnie zainicjować kontener, zastosowaliśmy klasyczny dla systemów uniksowych wzorzec podwójnego rozwidlenia procesu.

#### 1. Pierwszy fork (Dziecko 1): 

Główny proces (host) tworzy proces potomny. W tym procesie tworzymy nową grupę kontrolną (Cgroups), a następnie wywołujemy funkcję systemową unshare(), tworząc nowe przestrzenie nazw (m.in. sieciową, montowania i PID). Zgodnie ze specyfikacją jądra, proces wywołujący unshare z flagą CLONE_NEWPID nie zostaje przeniesiony do nowej przestrzeni PID – dopiero jego potomkowie będą w niej operować.

#### 2. Drugi fork (Dziecko 2):

Aby nasz kontener posiadał proces o identyfikatorze PID 1 (co jest wymagane do poprawnego działania m.in. wirtualnego systemu plików /proc), proces "Dziecko 1" dokonuje kolejnego rozwidlenia. Powstały w ten sposób proces "Dziecko 2" staje się właściwym procesem init (PID 1) w wyizolowanym środowisku. To on odpowiada za zamontowanie systemu plików i uruchomienie docelowej powłoki. Główny proces na hoście w tym samym czasie zajmuje się zestawieniem wirtualnych interfejsów sieciowych.

### Namespaces (Przestrzenie nazw): Zapewniają izolację na wielu płaszczyznach:

CLONE_NEWUTS: Niezależna nazwa hosta (hostname).

CLONE_NEWPID: Izolacja drzewa procesów (kontener widzi procesy począwszy od PID 1).

CLONE_NEWNS: Niezależne punkty montowania (izolacja systemu plików).

CLONE_NEWNET: Osobny, całkowicie wyizolowany stos sieciowy.

### Control Groups (Cgroups v2):
Mechanizm pozwalający na narzucenie twardego limitu pamięci RAM dla środowiska kontenera, co zapobiega monopolizacji zasobów hosta.

###OverlayFS: 
Zastosowaliśmy system plików warstwowych. Łączymy bazowy system plików w trybie tylko do odczytu (Alpine Linux) z tymczasową warstwą zapisu. Dzięki temu modyfikacje dokonywane wewnątrz kontenera nie wpływają na oryginalny obraz systemu.

###Wirtualizacja sieci (veth + NAT):
Tworzymy parę wirtualnych interfejsów sieciowych (veth). Jeden z nich pozostaje w głównej przestrzeni hosta, natomiast drugi zostaje przeniesiony do przestrzeni kontenera. Całość ruchu sieciowego jest kierowana przez zdefiniowane reguły iptables (Maskarada/NAT), aby zapewnić kontenerowi dostęp do sieci zewnętrznej.

## Automatyzacja Procesów:
Proces budowania i testowania projektu został w pełni zautomatyzowany, co znacząco usprawnia cykl deweloperski:
*Makefile: Zamiast konieczności zapamiętywania złożonych poleceń operujących na uprawnieniach administracyjnych, wprowadziliśmy proste cele (targets):

**''make prepare'' – automatycznie pobiera i wypakowuje system plików RootFS (dystrybucja Alpine).

**''make run'' – uruchamia środowisko kontenerowe z nałożonymi limitami.

**''make test'' – weryfikuje poprawne działanie izolacji i zdolność kontenera do wykonania zadanego polecenia.

**''make clean'' - Usuwa pobrane pliki rootfs i przywraca repozytorium do stanu początkowego.

*GitHub Actions (CI Pipeline): Każde wypchnięcie kodu (push) lub Pull Request do gałęzi main bądź master wyzwala zdefiniowany potok automatyzacji (main.yml), który:

1. Przygotowuje czyste środowisko testowe w oparciu o system Ubuntu.

2. Prowizjonuje wymagany system plików (RootFS).

3. Uruchamia testy automatyczne, potwierdzając, że kod napisany w Pythonie integruje się bezbłędnie z niskopoziomowymi funkcjami systemu operacyjnego na maszynie CI.
 
---

## Wymagania wstępne

Aby uruchomić projekt, potrzeba:
 Systemu operacyjnego Linux (ze względu na specyficzne mechanizmy kernela, projekt nie zadziała natywnie na systemach Windows ani macOS).
 Python 3.x (korzysta wyłącznie z biblioteki standardowej).
 Uprawnień Roota (`sudo` jest wymagane do wywołań `unshare`, tworzenia interfejsów sieciowych i montowania systemów plików).
 Narzędzi standardowych `wget`, `tar`, `make`, `iptables`, `iproute2`.

---

## Szybki start

### 1. Przygotowanie środowiska
Poniższe polecenie pobierze minimalistyczną dystrybucję Alpine Linux, która posłuży jako główny system plików dla kontenera.
```bash
make prepare
```

### 2. Uruchomienie kontenera
Poniższe polecenie uruchamia izolowane środowisko z interaktywną powłoką. System domyślnie nałoży limit 100MB RAM.
```bash
make run
```
Po chwili pojawi się znak # wewnątrz kontenera. Można przetestować izolację:

hostname -> Można zobaczyć unikalną nazwę hosta (np. mini-abcde).

ps aux -> Można zobaczyć, że powłoka ma PID 1.

ping 8.8.8.8 -> Można sprawdzić, że kontener ma dostęp do Internetu przez NAT.

### 3. Zautomatyzowane testowanie
Poniższe polecenie uruchamia test weryfikujący poprawność działania mechanizmów bez wchodzenia w interakcję z powłoką kontenera.
```bash
make test
```
### 4. Sprzątanie środowiska
Usuń pobrane pliki rootfs i przywróć repozytorium do stanu początkowego.
```bash
make clean
```
## Struktura projektu
projekt_kontener.py – główny moduł aplikacyjny, zawierający logikę zarządzania przestrzeniami nazw, procesami (double fork) i siecią.

prepare_rootfs.sh – skrypt odpowiedzialny za bezpieczne pobranie i rozpakowanie systemu bazowego z zachowaniem uprawnień roota.

Makefile – plik konfiguracyjny narzędzia make, centralizujący komendy projektowe.

.github/workflows/main.yml – definicja procesów ciągłej integracji (CI) dla GitHub Actions.

.gitignore – konfiguracja zapobiegająca wysyłaniu pobranych archiwów RootFS oraz plików tymczasowych do repozytorium.
## Zastrzeżenie (Disclaimer)
Ten projekt ma charakter wyłącznie edukacyjny. Ze względu na uproszczoną implementację i pominięcie zaawansowanych mechanizmów bezpieczeństwa (np. seccomp profiles, AppArmor/SELinux, drop capabilities), nie jest to narzędzie przeznaczone do uruchamiania w środowisku produkcyjnym.
