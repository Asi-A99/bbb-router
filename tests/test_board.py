"""Hardware-in-the-loop checks: run commands on the real BeagleBone over SSH.

Needs key-based SSH to the board (ssh-copy-id) and passwordless sudo on the
board for the two read-only commands used below (/etc/sudoers.d/bbr-tests).

Board checks only:   python3 -m pytest -v -m hardware
"""
import json
import os
import subprocess

import pytest

BOARD = os.environ.get("BBR_BOARD", "debian@192.168.50.2")

pytestmark = pytest.mark.hardware           # marks every test in this file


def board(cmd):
    """Run cmd on the board over SSH and return its output; fail the test if it fails."""
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", BOARD, cmd]
    # Under "sudo pytest", ssh would run as root and miss your key, so run it as you.
    if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
        ssh = ["sudo", "-u", os.environ["SUDO_USER"]] + ssh
    r = subprocess.run(ssh, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        pytest.fail(f"on the board, {cmd!r} failed: {r.stderr.strip()}")
    return r.stdout


@pytest.fixture(scope="module", autouse=True)
def board_reachable():
    """Try SSH once, so a powered-off board gives one clear error, not four timeouts."""
    board("true")


def test_kernel_is_ours():
    release = board("uname -r").strip()
    assert release.endswith("-bbr"), f"board is running {release}"


def test_firewall_ruleset_loaded():
    objs = json.loads(board("sudo -n nft -j list ruleset"))["nftables"]
    chains = {(o["chain"]["table"], o["chain"]["name"]): o["chain"]
              for o in objs if "chain" in o}
    assert ("filter", "forward") in chains, "inet filter table is not loaded"
    assert chains[("filter", "input")]["policy"] == "drop"
    assert chains[("filter", "forward")]["policy"] == "drop"
    rules = [o["rule"] for o in objs if "rule" in o]
    assert any(r["chain"] == "postrouting" and any("masquerade" in e for e in r["expr"])
               for r in rules), "no masquerade rule loaded"


def test_ospf_neighbour_full():
    out = board("sudo -n vtysh -c 'show ip ospf neighbor'")
    assert "Full" in out, f"no OSPF neighbour in Full state:\n{out}"


def test_bbr_count_loaded():
    assert "bbr_count" in board("lsmod"), "bbr_count module is not loaded"
