"""Namespace tests for the board's real firewall (config/nftables.conf).

Five namespaces stand in for the real networks:

    t-lan    --- end0            \
    t-office --- end0.10          >  t-r1 (loads config/nftables.conf)  --- enx00e8004fc6eb --- t-wan
    t-guest  --- end0.20         /

Run from the repo root:  sudo python3 -m pytest -v tests/test_router.py
"""
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

CONF = Path(__file__).resolve().parent.parent / "config" / "nftables.conf"

# The router-side names must match the defines at the top of config/nftables.conf.
LAN_IF, OFFICE_IF, GUEST_IF, WAN_IF = "end0", "end0.10", "end0.20", "enx00e8004fc6eb"

# Addresses are free to choose: the ruleset only matches interface names.
LAN_HOST, R1_LAN = "192.168.50.10", "192.168.50.2"
OFFICE_HOST, R1_OFFICE = "10.10.10.10", "10.10.10.1"
GUEST_HOST, R1_GUEST = "10.10.20.10", "10.10.20.1"
WAN_HOST, R1_WAN = "203.0.113.1", "203.0.113.2"     # 203.0.113.0/24 is reserved for examples

NAMESPACES = ["t-lan", "t-office", "t-guest", "t-r1", "t-wan"]

# (host namespace, host device, host address, router device, router address)
LINKS = [
    ("t-lan", "lan0", LAN_HOST, LAN_IF, R1_LAN),
    ("t-office", "off0", OFFICE_HOST, OFFICE_IF, R1_OFFICE),
    ("t-guest", "gst0", GUEST_HOST, GUEST_IF, R1_GUEST),
    ("t-wan", "wan0", WAN_HOST, WAN_IF, R1_WAN),
]


def sh(cmd):
    """Run cmd; raise CalledProcessError if it fails."""
    return subprocess.run(cmd, shell=True, check=True,
                          capture_output=True, text=True).stdout


def ok(cmd):
    """Run cmd; return True if it succeeded (for checks that are expected to fail)."""
    return subprocess.run(cmd, shell=True, capture_output=True).returncode == 0


def ping(ns, ip):
    return ok(f"ip netns exec {ns} ping -c 1 -W 1 {ip}")


def tcp_open(ns, ip, port):
    """True if a TCP connection from namespace ns to ip:port succeeds within 2 s."""
    return ok(f"ip netns exec {ns} timeout 2 bash -c 'exec 3<>/dev/tcp/{ip}/{port}'")


@contextmanager
def tcp_listener(ns, port):
    """Run a small TCP server on port inside namespace ns while the with-block runs."""
    proc = subprocess.Popen(
        ["ip", "netns", "exec", ns, "python3", "-m", "http.server", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):                         # wait up to 5 s for it to listen
            if sh(f"ip netns exec {ns} ss -Htln 'sport = :{port}'").strip():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError(f"listener on port {port} in {ns} did not start")
        yield
    finally:
        proc.terminate()
        proc.wait()


def setup_commands():
    """Every command that builds the topology, in order.

    Keeping setup as a list makes it easy for a test to break it on purpose."""
    cmds = []
    for ns in NAMESPACES:
        cmds += [f"ip netns add {ns}",
                 f"ip -n {ns} link set lo up"]
    for ns, dev, addr, rdev, raddr in LINKS:
        # create the pair with the router end already carrying the board's name
        cmds += [f"ip link add {dev} netns {ns} type veth peer name {rdev} netns t-r1",
                 f"ip -n {ns} addr add {addr}/24 dev {dev}",
                 f"ip -n t-r1 addr add {raddr}/24 dev {rdev}",
                 f"ip -n {ns} link set {dev} up",
                 f"ip -n t-r1 link set {rdev} up"]
        if ns != "t-wan":           # the WAN side has no route back to private subnets
            cmds.append(f"ip -n {ns} route add default via {raddr}")
    cmds += ["ip netns exec t-r1 sysctl -qw net.ipv4.ip_forward=1",
             f"ip netns exec t-r1 nft -f {CONF}"]
    return cmds


def existing_namespaces():
    """Names of our test namespaces that currently exist."""
    out = sh("ip netns list")
    names = {line.split()[0] for line in out.splitlines() if line.strip()}
    return [ns for ns in NAMESPACES if ns in names]


def cleanup():
    """Delete every test namespace that exists. Never fails.

    Deleting a namespace also deletes the interfaces inside it, and deleting
    one end of a veth pair deletes the other end, so this removes everything."""
    for ns in NAMESPACES:
        ok(f"ip netns del {ns}")


@contextmanager
def topology(cmds):
    cleanup()                       # leftovers from a run that was killed
    try:
        for cmd in cmds:
            sh(cmd)
        yield
    finally:
        cleanup()                   # runs whether setup or the test passed or failed


@pytest.fixture
def router():
    with topology(setup_commands()):
        yield


def test_failed_setup_leaves_nothing_behind():
    cmds = setup_commands()
    cmds.insert(len(cmds) // 2, "false")        # break setup halfway on purpose
    with pytest.raises(subprocess.CalledProcessError):
        with topology(cmds):
            pass
    assert existing_namespaces() == []


# --- LAN <-> WAN ------------------------------------------------------------

def test_lan_reaches_wan(router):
    assert ping("t-lan", WAN_HOST)


def test_lan_needs_masquerade(router):
    """Proves the test above depends on NAT: without it, wan cannot reply."""
    sh("ip netns exec t-r1 nft delete table ip nat")
    assert not ping("t-lan", WAN_HOST)


def test_lan_opens_tcp_to_wan(router):
    with tcp_listener("t-wan", 8080):
        assert tcp_open("t-lan", WAN_HOST, 8080)


def test_wan_cannot_reach_lan_even_with_route(router):
    sh(f"ip -n t-wan route add 192.168.50.0/24 via {R1_WAN}")
    assert not ping("t-wan", LAN_HOST)
    with tcp_listener("t-lan", 8080):
        assert tcp_open("t-lan", LAN_HOST, 8080)        # the listener works...
        assert not tcp_open("t-wan", LAN_HOST, 8080)    # ...but wan cannot reach it


# --- Guest VLAN rules (Day 4) -------------------------------------------------

def test_guest_reaches_wan(router):
    assert ping("t-guest", WAN_HOST)


def test_office_reaches_wan(router):
    assert ping("t-office", WAN_HOST)


def test_guest_cannot_reach_office(router):
    assert not ping("t-guest", OFFICE_HOST)


def test_guest_cannot_ssh_to_router(router):
    with tcp_listener("t-r1", 22):
        assert tcp_open("t-lan", R1_LAN, 22)            # LAN may log in
        assert not tcp_open("t-guest", R1_GUEST, 22)    # guest may not
