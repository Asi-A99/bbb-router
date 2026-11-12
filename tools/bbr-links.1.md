---
title: BBR-LINKS
section: 1
header: User Commands
footer: bbr-tools 0.1
date: November 2026
---

# NAME

bbr-links - list network interfaces and watch link changes using rtnetlink

# SYNOPSIS

**bbr-links** [**\--watch**]

# DESCRIPTION

**bbr-links** asks the kernel for every network interface over an rtnetlink
socket (an **RTM_GETLINK** dump request) and prints one line per interface:
index, name, state, MTU, link-layer address, and received and transmitted
packet counts.

The state is **UP** when the interface is administratively up and has carrier,
**NO-CARRIER** when it is up but no cable or link partner is detected, and
**DOWN** when it is administratively down.

# OPTIONS

**\--watch**
:   After printing the list, join the **RTMGRP_LINK** multicast group and print
    a time-stamped line whenever an interface changes state, appears or is
    removed. Runs until interrupted.

# EXIT STATUS

**0** on success, **1** if the netlink socket cannot be created, bound or used.

# EXAMPLES

List interfaces:

    bbr-links

Watch the WAN link while unplugging its cable:

    bbr-links --watch

# SEE ALSO

**ip-link**(8), **netlink**(7), **rtnetlink**(7)
