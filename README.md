# Projekt_Kontener Edukacyjny Silnik Konteneryzacji w Pythonie

Projekt_Kontener to lekki silnik konteneryzacji napisany od zera. Projekt został stworzony w celach edukacyjnych, aby zrozumieć mechanizmy izolacji procesów w jądrze Linuxa oraz zaprezentować dobre praktyki z zakresu automatyzacji infrastruktury (Infrastructure as Code).

Projekt nie korzysta z gotowych bibliotek do konteneryzacji. Cała magia opiera się na bezpośrednich wywołaniach systemowych (syscalls) do jądra Linuxa za pomocą biblioteki `ctypes` w Pythonie oraz na skryptach automatyzujących środowisko.

---

## Główne funkcjonalności

Projekt łączy w sobie zagadnienia z dwóch głównych dziedzin inżynierii oprogramowania

### 1. Inżynieria Systemów Operacyjnych (Low-Level Linux)
 * **Izolacja Procesów (Namespaces) Wykorzystanie syscalla `unshare` do separacji drzewa procesów (`CLONE_NEWPID`), nazwy hosta (`CLONE_NEWUTS`), punktów montowania (`CLONE_NEWNS`) oraz stosu sieciowego (`CLONE_NEWNET`).
 * **Zarządzanie Zasobami (Cgroups) Ręczna manipulacja wirtualnym systemem plików `/sys/fs/cgroup` w celu nakładania sztywnych limitów pamięci RAM na procesy potomne.
 * **Architektura Double-Fork Zastosowanie podwójnego rozwidlenia procesów (wzorzec ze środowiska `runC`), co gwarantuje poprawne zainicjowanie sieci przez hosta i przyznanie kontenerowi PID 1 wewnątrz jego izolowanej przestrzeni.
 * **Efemeryczny System Plików (OverlayFS) Kontenery nie modyfikują bazowego obrazu systemu. Wszystkie zmiany zapisywane są w ulotnej warstwie (upperdir), co pozwala na uruchamianie wielu niezależnych środowisk z jednego obrazu.
 * **Własny Stos Sieciowy i NAT Wirtualne kable (`veth`), dynamiczne przydzielanie prywatnych adresów IP w przestrzeni kontenera oraz konfiguracja `iptables` (Masquerade) na hoście, by zapewnić kontenerowi dostęp do Internetu.

### 2. Automatyzacja Procesów (DevOps & IaC)
 Prowizjonowanie Środowiska Skrypt Bash (`prepare_rootfs.sh`), który w sposób idempotentny pobiera i rozpakowuje minimalny system plików (Alpine Linux).
 Orkiestracja (Makefile) Deklaratywne zarządzanie cyklem życia aplikacji. Całość obsługiwana jest prostymi komendami `make`.
 Zautomatyzowane Testy (CICD) Zbudowany cel `make test`, który podnosi całą skomplikowaną architekturę, weryfikuje połączenie, wykonuje komendę wewnątrz izolowanego środowiska i bezpiecznie sprząta zasoby.

---

## Wymagania wstępne

Aby uruchomić projekt, potrzebujesz
 Systemu operacyjnego Linux (ze względu na specyficzne mechanizmy kernela, projekt nie zadziała natywnie na systemach Windows ani macOS).
 Python 3.x (korzysta wyłącznie z biblioteki standardowej).
 Uprawnień Roota (`sudo` jest wymagane do wywołań `unshare`, tworzenia interfejsów sieciowych i montowania systemów plików).
 Narzędzi standardowych `wget`, `tar`, `make`, `iptables`, `iproute2`.

---

## Szybki start (Quick Start)

### 1. Przygotowanie środowiska
Pobierz projekt i użyj zautomatyzowanego skryptu, aby pobrać i przygotować główny system plików (RootFS).
```bash
make prepare
```
(Skrypt pobierze minimalny obraz Alpine Linux i rozpakuje go do folderu ./alpine_root. Proces ten jest idempotentny.)

### 2. Uruchomienie kontenera
Uruchom izolowane środowisko z interaktywną powłoką. System domyślnie nałoży limit 100MB RAM.
```bash
make run
```
Po chwili powinieneś zobaczyć znak # wewnątrz kontenera. Możesz przetestować izolację:

hostname -> Zobaczysz unikalną nazwę hosta (np. mini-abcde).

ps aux -> Zobaczysz, że powłoka ma PID 1.

ping 8.8.8.8 -> Sprawdzisz, że kontener ma dostęp do Internetu przez NAT.

### 2. Zautomatyzowane testowanie
Uruchom test weryfikujący poprawność cyklu życia kontenera.
```bash
make test
```
### 4. Sprzątanie środowiska
Usuń pobrane pliki rootfs i przywróć repozytorium do stanu początkowego.
```bash
make clean
```
## Struktura projektu
- mini_docker.py - Główne "serce" projektu. Odpowiada za syscalls, zarządzanie cyklem życia procesu (Double-Fork), konfigurację sieci veth i montowanie systemu plików.

- prepare_rootfs.sh - Skrypt Bash automatyzujący pobieranie lekkiego obrazu systemu (Alpine RootFS).

- Makefile - Interfejs do zarządzania procesem automatyzacji i cyklem życia środowiska.

## Zastrzeżenie (Disclaimer)
Ten projekt ma charakter wyłącznie edukacyjny. Ze względu na uproszczoną implementację i pominięcie zaawansowanych mechanizmów bezpieczeństwa (np. seccomp profiles, AppArmor/SELinux, drop capabilities), nie jest to narzędzie przeznaczone do uruchamiania w środowisku produkcyjnym.
