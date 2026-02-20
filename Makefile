# Definicje zmiennych
PYTHON = python3
SCRIPT = projekt_kontener.py
ROOTFS = ./alpine_root
MEM_LIMIT = 100

.PHONY: all prepare run clean test help

all: prepare

#Pomoc
help:
	@echo "Dostępne komendy:"
	@echo "  make prepare  - Pobiera i rozpakowuje system plików (rootfs)"
	@echo "  make run      - Uruchamia kontener (wymaga sudo)"
	@echo "  make clean    - Usuwa pobrany system plików"
	@echo "  make test     - Uruchamia test automatyczny (czy kontener działa?)"

#Przygotowanie środowiska
prepare:
	@./prepare_rootfs.sh

#Uruchomienie
run: prepare
	@echo "[*] Uruchamianie kontenera z limitem RAM $(MEM_LIMIT)MB..."
	@sudo $(PYTHON) $(SCRIPT) --rootfs $(ROOTFS) --mem $(MEM_LIMIT)

#Sprzątanie
clean:
	@echo "[*] Usuwanie rootfs..."
	@sudo rm -rf $(ROOTFS)
	@echo "[*] Wyczyszczono."

#Test; uruchamia kontener, wykonuje 'echo', i sprawdza czy bez błędu
test: prepare
	@echo "[TEST] Sprawdzanie czy kontener potrafi wykonać komendę..."
	@sudo $(PYTHON) $(SCRIPT) --rootfs $(ROOTFS) --cmd "echo 'Hello from Container'"
	@echo "[TEST] Sukces!"
