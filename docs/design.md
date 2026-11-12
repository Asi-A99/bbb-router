## Non-goals
- There is no IPv6 firewall
- This is not production hardened
- There is no Wi-Fi included in the router

##Packet Path
1. cpsw DMA receives the frame.
2. XDP runs, before any sk_buff exists.
3. The sk_buff is built.
4. Netfilter prerouting runs, including conntrack.
5. The routing decision is made.
6. The forward chain runs: your filter rules, then bbr_count (priority FIRST).
7. Postrouting applies masquerade.
8. The WAN queue (qdisc) holds the packet.
9. usbnet hands it to the SR9700.
10. The packet reaches the home router.
