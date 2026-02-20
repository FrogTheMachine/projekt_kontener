import os
import sys
import ctypes
import subprocess
import argparse
import random
import string
import time

CLONE_NEWNS  = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000

libc = ctypes.CDLL('libc.so.6')


def rand():
    return ''.join(random.choices(string.ascii_lowercase, k=5))


def set_hostname(name):
    libc.sethostname(name.encode(), len(name))


# ---------------- OVERLAY ----------------

def setup_overlay(rootfs, cid):
    base = f"/tmp/projekt_kontener/{cid}"
    upper = f"{base}/upper"
    work = f"{base}/work"
    merged = f"{base}/merged"

    os.makedirs(upper, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    os.makedirs(merged, exist_ok=True)

    os.system(
        f"mount -t overlay overlay "
        f"-o lowerdir={rootfs},upperdir={upper},workdir={work} "
        f"{merged}"
    )

    return merged


# ---------------- NETWORK ----------------

def setup_network(pid, cid):
    veth_host = f"vethh-{cid}"
    veth_cont = f"vethc-{cid}"

    # Tworzenie pary veth
    os.system(f"ip link add {veth_host} type veth peer name {veth_cont}")
    # Przeniesienie jednego końca do netns kontenera
    os.system(f"ip link set {veth_cont} netns {pid}")

    # Konfiguracja po stronie Hosta
    ip_host = random.randint(2, 200)
    os.system(f"ip addr add 10.0.{ip_host}.1/24 dev {veth_host}")
    os.system(f"ip link set {veth_host} up")

    # Konfiguracja po stronie Kontenera
    os.system(f"nsenter -t {pid} -n ip addr add 10.0.{ip_host}.2/24 dev {veth_cont}")
    os.system(f"nsenter -t {pid} -n ip link set {veth_cont} up")
    os.system(f"nsenter -t {pid} -n ip link set lo up")
    
    # Dodanie domyślnej bramy (routing wewnątrz kontenera)
    os.system(f"nsenter -t {pid} -n ip route add default via 10.0.{ip_host}.1")

    # NAT i Forwarding na Hoście
    os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")
    os.system(f"iptables -t nat -A POSTROUTING -s 10.0.{ip_host}.0/24 -j MASQUERADE")


# ---------------- CGROUP ----------------

def create_cgroup(pid, mem):
    path = f"/sys/fs/cgroup/mini_{pid}"
    os.makedirs(path, exist_ok=True)

    with open(f"{path}/cgroup.procs", "w") as f:
        f.write(str(pid))

    if mem:
        with open(f"{path}/memory.max", "w") as f:
            f.write(str(int(mem)*1024*1024))


# ---------------- CONTAINER ----------------

def container_entry(cmd, rootfs, cid):
    set_hostname(f"mini-{cid}")
    merged = setup_overlay(rootfs, cid)

    os.chroot(merged)
    os.chdir("/")

    os.makedirs("/proc", exist_ok=True)
    os.system("mount -t proc proc /proc")

    # [FIX] Czekamy chwilę, aż host skonfiguruje interfejsy sieciowe (veth) i NAT
    time.sleep(5)

    try:
        subprocess.run(cmd, shell=True)
    finally:
        # Sprzątanie wnętrza
        os.system("umount /proc")
        
        # Sprzątanie OverlayFS i katalogów (bezpieczne wyjście do roota)
        # Opuść chroot z powrotem do / (potrzebne do umount OverlayFS w głównym namespace'ie mountowania,
        # chociaż technicznie CLONE_NEWNS to izoluje, lepiej odmontować na koniec).

# ---------------- MAIN ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootfs", required=True)
    parser.add_argument("--cmd", default="/bin/sh")
    parser.add_argument("--mem")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("sudo required")
        sys.exit(1)

    cid = rand()

    if libc.unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET) != 0:
        print("namespace error")
        sys.exit(1)

    pid = os.fork()

    if pid == 0:
        container_entry(args.cmd, args.rootfs, cid)
    else:
        setup_network(pid, cid)

        if args.mem:
            create_cgroup(pid, args.mem)

        print(f"[mini-docker] container pid: {pid}")
        os.waitpid(pid, 0)


if __name__ == "__main__":
    main()
