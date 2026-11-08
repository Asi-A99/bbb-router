#!/bin/bash
set -e
for ns in h1 h2 r1; do sudo ip netns add $ns; done
sudo ip link add h1-r1 netns h1 type veth peer name r1-h1 netns r1
sudo ip link add h2-r1 netns h2 type veth peer name r1-h2 netns r1
sudo ip -n h1 addr add 10.0.1.10/24 dev h1-r1
sudo ip -n r1 addr add 10.0.1.1/24  dev r1-h1
sudo ip -n h2 addr add 10.0.2.10/24 dev h2-r1
sudo ip -n r1 addr add 10.0.2.1/24  dev r1-h2
for ns in h1 h2 r1; do sudo ip -n $ns link set lo up; done
sudo ip -n h1 link set h1-r1 up; sudo ip -n r1 link set r1-h1 up
sudo ip -n h2 link set h2-r1 up; sudo ip -n r1 link set r1-h2 up
sudo ip -n h1 route add default via 10.0.1.1
sudo ip -n h2 route add default via 10.0.2.1

