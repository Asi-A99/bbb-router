#!/usr/bin/env python3
"""topo.py: build or remove the Day 1 router topology (h1 - r1 - h2)."""
import subprocess
import sys

NAMESPACES = ["h1", "h2", "r1"]


def sh(cmd):
    """Run one shell command; stop with an error if it fails."""
    print(f"+ {cmd}")
    subprocess.run(cmd, shell=True, check=True)


def up():
    for ns in NAMESPACES:
        sh(f"ip netns add {ns}")
    sh("ip link add h1-r1 netns h1 type veth peer name r1-h1 netns r1")
    sh("ip link add h2-r1 netns h2 type veth peer name r1-h2 netns r1")

    # 3. addresses
    sh("ip -n h1 addr add 10.255.1.10/24 dev h1-r1")
    sh("ip -n r1 addr add 10.255.1.1/24 dev r1-h1")
    sh("ip -n h2 addr add 10.255.2.10/24 dev h2-r1")
    sh("ip -n r1 addr add 10.255.2.1/24 dev r1-h2")

    # 4. bring interfaces up
    for ns in NAMESPACES:
        sh(f"ip -n {ns} link set lo up")
    sh("ip -n h1 link set h1-r1 up")
    sh("ip -n r1 link set r1-h1 up")
    sh("ip -n h2 link set h2-r1 up")
    sh("ip -n r1 link set r1-h2 up")

    # 5. default routes: each host sends other traffic to r1
    sh("ip -n h1 route add default via 10.255.1.1")
    sh("ip -n h2 route add default via 10.255.2.1")

    # TODO: translate the rest of topo.sh, one sh(...) call per line:
    #   the second veth pair, the four addresses, lo up in each namespace,
    #   the four veth ends up, and the two default routes


def down():
    for ns in NAMESPACES:
        # no check=True here: deleting a namespace that is already gone is fine
        subprocess.run(f"ip netns del {ns}", shell=True)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("up", "down"):
        print("usage: sudo python3 topo.py up|down")
        sys.exit(2)
    if sys.argv[1] == "up":
        up()
    else:
        down()


if __name__ == "__main__":
    main()
