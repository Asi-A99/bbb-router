#!/bin/bash
set -e
for ns in b1 b2 b3 sw; do sudo ip netns add $ns; done
sudo ip -n sw link add br0 type bridge
sudo ip link add b1-sw netns b1 type veth peer name sw-b1 netns sw
sudo ip link add b2-sw netns b2 type veth peer name sw-b2 netns sw
sudo ip link add b3-sw netns b3 type veth peer name sw-b3 netns sw
sudo ip -n sw link set sw-b1 master br0
sudo ip -n sw link set sw-b2 master br0
sudo ip -n sw link set sw-b3 master br0
sudo ip -n b1 addr add 10.0.2.1/24 dev b1-sw
sudo ip -n b2 addr add 10.0.2.2/24 dev b2-sw
sudo ip -n b3 addr add 10.0.2.3/24 dev b3-sw
for ns in b1 b2 b3 sw; do sudo ip -n $ns link set lo up; done
sudo ip -n b1 link set b1-sw up
sudo ip -n b2 link set b2-sw up
sudo ip -n b3 link set b3-sw up
sudo ip -n sw link set br0 up
sudo ip -n sw link set sw-b1 up
sudo ip -n sw link set sw-b2 up
sudo ip -n sw link set sw-b3 up

