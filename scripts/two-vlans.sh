#!/bin/bash
set -e

sudo ip netns add office
sudo ip link add link eno0 name vlan10 type vlan id 10
sudo ip link set vlan10 netns office
sudo ip -n office addr add 192.168.10.1/24 dev vlan10
sudo ip -n office link set lo up
sudo ip -n office link set vlan10 up
sudo ip -n office route add default via 192.168.10.2

sudo ip netns add guest
sudo ip link add link eno0 name vlan20 type vlan id 20
sudo ip link set vlan20 netns guest
sudo ip -n guest addr add 192.168.20.1/24 dev vlan20
sudo ip -n guest link set lo up
sudo ip -n guest link set vlan20 up
sudo ip -n guest route add default via 192.168.20.2
