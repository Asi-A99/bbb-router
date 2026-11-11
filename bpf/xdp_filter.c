#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define BLOCKED_PORT 5201

/* One counter per IP protocol number (1 = ICMP, 6 = TCP, 17 = UDP ...) */
struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 256);
	__type(key, __u32);
	__type(value, __u64);
} proto_count SEC(".maps");

/* A single counter: packets this program dropped */
struct {
	__uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} drop_count SEC(".maps");

SEC("xdp")
int xdp_filter(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	struct ethhdr *eth = data;
	struct iphdr *ip;
	struct udphdr *udp;
	__u32 key;
	__u64 *val;

	if ((void *)(eth + 1) > data_end)
		return XDP_PASS;
	if (eth->h_proto != bpf_htons(ETH_P_IP))
		return XDP_PASS;

	ip = (void *)(eth + 1);
	if ((void *)(ip + 1) > data_end)
		return XDP_PASS;

	key = ip->protocol;
	val = bpf_map_lookup_elem(&proto_count, &key);
	if (val)
		(*val)++;

	if (ip->protocol != IPPROTO_UDP)
		return XDP_PASS;
	if (ip->ihl < 5)
		return XDP_PASS;

	/* the IP header can carry options, so its length is ihl * 4 bytes */
	udp = (void *)ip + ip->ihl * 4;
	if ((void *)(udp + 1) > data_end)	/* the extra bounds check */
		return XDP_PASS;

	if (udp->dest != bpf_htons(BLOCKED_PORT))
		return XDP_PASS;

	key = 0;
	val = bpf_map_lookup_elem(&drop_count, &key);
	if (val)
		(*val)++;
	return XDP_DROP;
}

char LICENSE[] SEC("license") = "GPL";
