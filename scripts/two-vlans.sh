#!/bin/bash
set -e 

for i in 10 20; do
  sudo ip netns add n$i
  sudo ip link add veth-n$i type veth peer name eno0 netns n$i
  sudo ip addr add 10.10.$i.1/24 dev veth-n$i && sudo ip link set veth-n$i up
  sudo ip -n n$i addr add 10.10.$i.10/24 dev eno0
  sudo ip -n n$i link set eno0 up && sudo ip -n n$i link set lo up
  sudo ip -n n$i route add default via 10.10.$i.1
done
sudo sysctl -w net.ipv4.ip_forward=1

