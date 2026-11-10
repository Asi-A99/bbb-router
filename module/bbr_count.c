// SPDX-License-Identifier: GPL-2.0
/* bbr_count: count forwarded IPv4 packets with a netfilter hook */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/skbuff.h>
#include <linux/atomic.h>
#include <net/net_namespace.h>

static atomic64_t fwd_packets = ATOMIC64_INIT(0);

static unsigned int bbr_hook(void *priv, struct sk_buff *skb,
        const struct nf_hook_state *state)
{
 const struct iphdr *iph = ip_hdr(skb);

 atomic64_inc(&fwd_packets);
 pr_debug("fwd %pI4 -> %pI4 proto %u out %s\n", &iph->saddr, &iph->daddr,
   iph->protocol, state->out ? state->out->name : "?");
 return NF_ACCEPT;
}

static const struct nf_hook_ops bbr_ops = {
 .hook     = bbr_hook,
 .pf       = NFPROTO_IPV4,
 .hooknum  = NF_INET_FORWARD,
 .priority = NF_IP_PRI_FIRST,
};

static int __init bbr_init(void)
{
 int ret = nf_register_net_hook(&init_net, &bbr_ops);

 if (!ret)
  pr_info("loaded\n");
 return ret;
}

static void __exit bbr_exit(void)
{
 nf_unregister_net_hook(&init_net, &bbr_ops);
 pr_info("unloaded after %lld forwarded packets\n",
  (long long)atomic64_read(&fwd_packets));
}

module_init(bbr_init);
module_exit(bbr_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("BeagleBone router: count forwarded IPv4 packets");

