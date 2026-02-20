# 🐳 Mini-Docker Edukacyjny Silnik Konteneryzacji w Pythonie

Mini-Docker to autorski, lekki silnik konteneryzacji napisany całkowicie od zera. Projekt został stworzony w celach edukacyjnych, aby dogłębnie zrozumieć mechanizmy izolacji procesów w jądrze Linuxa oraz zaprezentować dobre praktyki z zakresu automatyzacji infrastruktury (Infrastructure as Code).

Projekt nie korzysta z gotowych bibliotek do konteneryzacji. Cała magia opiera się na bezpośrednich wywołaniach systemowych (syscalls) do jądra Linuxa za pomocą biblioteki `ctypes` w Pythonie oraz na skryptach automatyzujących środowisko.

---

## 🚀 Główne funkcjonalności

Projekt łączy w sobie zagadnienia z dwóch głównych dziedzin inżynierii oprogramowania

### 1. Inżynieria Systemów Operacyjnych (Low-Level Linux)
 Izolacja Procesów (Namespaces) Wykorzystanie syscalla `unshare` do separacji drzewa procesów (`CLONE_NEWPID`), nazwy hosta (`CLONE_NEWUTS`), punktów montowania (`CLONE_NEWNS`) oraz stosu sieciowego (`CLONE_NEWNET`).
 Zarządzanie Zasobami (Cgroups) Ręczna manipulacja wirtualnym systemem plików `sysfscgroup` w celu nakładania sztywnych limitów pamięci RAM na procesy potomne.
 Architektura Double-Fork Zastosowanie podwójnego rozwidlenia procesów (wzorzec ze środowiska `runC`), co gwarantuje poprawne zainicjowanie sieci przez hosta i przyznanie kontenerowi PID 1 wewnątrz jego izolowanej przestrzeni.
 Efemeryczny System Plików (OverlayFS) Kontenery nie modyfikują bazowego obrazu systemu. Wszystkie zmiany zapisywane są w ulotnej warstwie (upperdir), co pozwala na uruchamianie wielu niezależnych środowisk z jednego obrazu.
 Własny Stos Sieciowy i NAT Wirtualne kable (`veth`), dynamiczne przydzielanie prywatnych adresów IP w przestrzeni kontenera oraz konfiguracja `iptables` (Masquerade) na hoście, by zapewnić kontenerowi dostęp do Internetu.

### 2. Automatyzacja Procesów (DevOps & IaC)
 Prowizjonowanie Środowiska Skrypt Bash (`prepare_rootfs.sh`), który w sposób idempotentny pobiera i rozpakowuje minimalny system plików (Alpine Linux).
 Orkiestracja (Makefile) Deklaratywne zarządzanie cyklem życia aplikacji. Całość obsługiwana jest prostymi komendami `make`.
 Zautomatyzowane Testy (CICD) Zbudowany cel `make test`, który podnosi całą skomplikowaną architekturę, weryfikuje połączenie, wykonuje komendę wewnątrz izolowanego środowiska i bezpiecznie sprząta zasoby.

---

## 🛠️ Wymagania wstępne

Aby uruchomić projekt, potrzebujesz
 Systemu operacyjnego Linux (ze względu na specyficzne mechanizmy kernela, projekt nie zadziała natywnie na systemach Windows ani macOS).
 Python 3.x (korzysta wyłącznie z biblioteki standardowej).
 Uprawnień Roota (`sudo` jest wymagane do wywołań `unshare`, tworzenia interfejsów sieciowych i montowania systemów plików).
 Narzędzi standardowych `wget`, `tar`, `make`, `iptables`, `iproute2`.

---

## 📦 Szybki start (Quick Start)

### 1. Przygotowanie środowiska
Pobierz projekt i użyj zautomatyzowanego skryptu, aby pobrać i przygotować główny system plików (RootFS).
```bash
make prepare