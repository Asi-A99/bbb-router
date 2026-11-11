import subprocess
import pytest


def sh(cmd):
    return subprocess.run(cmd, shell=True, check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def two_hosts():
    sh("ip netns add h1")
    sh("ip netns add h2")
    sh("ip link add veth1 netns h1 type veth peer name veth2 netns h2")
    sh("ip -n h1 addr add 10.0.0.1/24 dev veth1")
    sh("ip -n h2 addr add 10.0.0.2/24 dev veth2")
    sh("ip -n h1 link set veth1 up")
    sh("ip -n h2 link set veth2 up")
    yield
    sh("ip netns del h1")
    sh("ip netns del h2")


def test_hosts_can_ping(two_hosts):
    sh("ip netns exec h1 ping -c 1 -W 1 10.0.0.2")


def test_wrong_subnet_cannot_ping(two_hosts):
    with pytest.raises(subprocess.CalledProcessError):
        sh("ip netns exec h1 ping -c 1 -W 1 10.0.9.9")

