import os
import sys
import ctypes
import subprocess
import argparse
import random
import string
import time

# --- DEFINICJE FLAG SYSTEMOWYCH ---
CLONE_NEWNS  = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000

libc = ctypes.CDLL('libc.so.6')

def rand():
    return ''.join(random.choices(string.ascii_lowercase, k=5))

def set_hostname(name):
    libc.sethostname(name.encode(), len(name))

# ---------------- OVERLAYFS ----------------

def setup_overlay(rootfs, cid):
    # Używamy ścieżki bezwzględnej (ważne!)
    abs_rootfs = os.path.abspath(rootfs)
    
    base = f"/tmp/projekt_kontener/{cid}"
    upper = f"{base}/upper"
    work = f"{base}/work"
    merged = f"{base}/merged"

    os.makedirs(upper, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    os.makedirs(merged, exist_ok=True)

    cmd = f"mount -t overlay overlay -o lowerdir={abs_rootfs},upperdir={upper},workdir={work} {merged}"
    if os.system(cmd) != 0:
        print("[!] Błąd montowania OverlayFS!")
        sys.exit(1)

    return merged

# ---------------- SIECI ----------------

def setup_network(pid, cid):
    veth_host = f"vethh-{cid}"
    veth_cont = f"vethc-{cid}"
    
    # Losujemy podsieć, żeby unikać konfliktów
    ip_host = random.randint(2, 200)

    print(f"[*] Konfiguracja sieci dla PID {pid} (Podsieć: 10.0.{ip_host}.x)...")

    # 1. Tworzenie pary veth na HOŚCIE
    os.system(f"ip link add {veth_host} type veth peer name {veth_cont}")
    
    # 2. Przeniesienie veth_cont do przestrzeni DZIECKA
    os.system(f"ip link set {veth_cont} netns {pid}")

    # 3. Konfiguracja Hosta
    os.system(f"ip addr add 10.0.{ip_host}.1/24 dev {veth_host}")
    os.system(f"ip link set {veth_host} up")

    # 4. Konfiguracja Kontenera (przez nsenter)
    os.system(f"nsenter -t {pid} -n ip addr add 10.0.{ip_host}.2/24 dev {veth_cont}")
    os.system(f"nsenter -t {pid} -n ip link set {veth_cont} up")
    os.system(f"nsenter -t {pid} -n ip link set lo up")
    
    # 5. Routing (Brama domyślna)
    os.system(f"nsenter -t {pid} -n ip route add default via 10.0.{ip_host}.1")

    # 6. NAT (Maskarada)
    os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1")
    os.system(f"iptables -t nat -A POSTROUTING -s 10.0.{ip_host}.0/24 -j MASQUERADE")

# ---------------- CGROUPS ----------------

def create_cgroup(pid, mem):
    path = f"/sys/fs/cgroup/mini_{pid}"
    # Zabezpieczenie przed błędem na Ubuntu Desktop
    try:
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/cgroup.procs", "w") as f:
            f.write(str(pid))

        if mem:
            with open(f"{path}/memory.max", "w") as f:
                f.write(str(int(mem) * 1024 * 1024))
    except Exception as e:
        print(f"[!] Warning: Cgroups nie zadziałało (to normalne na niektórych Desktopach): {e}")

# ---------------- KONTENER (PID 1) ----------------

def container_entry(cmd, rootfs, cid):
    # Czekamy, aż Rodzic skonfiguruje sieć
    time.sleep(1)

    set_hostname(f"mini-{cid}")
    merged = setup_overlay(rootfs, cid)

    os.chroot(merged)
    os.chdir("/")

    os.makedirs("/proc", exist_ok=True)
    os.system("mount -t proc proc /proc")

    try:
        subprocess.run(cmd, shell=True)
    finally:
        os.system("umount /proc")
        # OverlayFS zostanie odmontowany przy restarcie systemu lub ręcznym czyszczeniu /tmp

# ---------------- MAIN (DOUBLE FORK) ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootfs", required=True)
    parser.add_argument("--cmd", default="/bin/sh")
    parser.add_argument("--mem")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[!] Błąd: Wymagane sudo")
        sys.exit(1)

    cid = rand()

    # --- FORK 1 ---
    pid1 = os.fork()

    if pid1 == 0:
        # === DZIECKO 1 (Przygotowanie) ===
        
        # Ustawiamy Cgroups na OBECNY proces (Dziecko 1),
        # Dziecko 2 to odziedziczy.
        if args.mem:
            create_cgroup(os.getpid(), args.mem)

        # TERAZ robimy unshare (wewnątrz dziecka, nie rodzica!)
        if libc.unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET) != 0:
            print("[!] Namespace error")
            sys.exit(1)

        # --- FORK 2 ---
        # Forkujemy się ponownie, żeby stać się PID 1 w nowej przestrzeni
        pid2 = os.fork()
        
        if pid2 == 0:
            # === DZIECKO 2 (Właściwy Kontener) ===
            container_entry(args.cmd, args.rootfs, cid)
        else:
            # Dziecko 1 kończy pracę i przekazuje pałeczkę
            os.waitpid(pid2, 0)
            sys.exit(0)

    else:
        # === RODZIC (Host) ===
        # Rodzic zostaje w normalnej sieci i konfiguruje interfejsy dla Dziecka 1
        
        # Czekamy chwilę, żeby Dziecko 1 zdążyło zrobić unshare
        time.sleep(0.5)
        
        setup_network(pid1, cid)

        print(f"[mini_kontener] Kontener uruchomiony. PID Hosta: {pid1}")
        os.waitpid(pid1, 0)

if __name__ == "__main__":
    main()