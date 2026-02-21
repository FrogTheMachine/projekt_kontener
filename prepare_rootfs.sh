#!/bin/bash

# Zatrzymanie skryptu w przypadku błędu
set -e

# Konfiguracja
ALPINE_VERSION="3.19.1"
ARCH="x86_64"
FILENAME="alpine-minirootfs-${ALPINE_VERSION}-${ARCH}.tar.gz"
URL="https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/${ARCH}/${FILENAME}"
ROOTFS_DIR="./alpine_root"

# Kolorki
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[*] Sprawdzanie środowiska...${NC}"

if [ -d "$ROOTFS_DIR" ]; then
    echo "Katalog $ROOTFS_DIR już istnieje. Pomijam pobieranie."
    exit 0
fi

echo -e "${GREEN}[*] Pobieranie Alpine Linux Minimal RootFS...${NC}"
wget -q --show-progress "$URL" -O "$FILENAME"

echo -e "${GREEN}[*] Rozpakowywanie systemu plików...${NC}"
mkdir -p "$ROOTFS_DIR"
# Używamy sudo tar, aby zachować uprawnienia plików wewnątrz archiwum (ważne dla roota)
sudo tar -xzf "$FILENAME" -C "$ROOTFS_DIR"

echo -e "${GREEN}[*] Sprzątanie...${NC}"
rm "$FILENAME"

echo -e "${GREEN}[SUCCESS] RootFS gotowy w katalogu: $ROOTFS_DIR${NC}"
