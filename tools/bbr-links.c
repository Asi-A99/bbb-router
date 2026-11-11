/* bbr-links: list network interfaces and packet counters using rtnetlink */
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <net/if.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <linux/if_link.h>

int main(void)
{
 int fd = socket(AF_NETLINK, SOCK_RAW | SOCK_CLOEXEC, NETLINK_ROUTE);
 if (fd < 0) {
  perror("socket");
  return 1;
 }

 struct {
  struct nlmsghdr nh;
  struct ifinfomsg ifi;
 } req = {
  .nh = {
   .nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg)),
   .nlmsg_type = RTM_GETLINK,
   .nlmsg_flags = NLM_F_REQUEST | NLM_F_DUMP,
   .nlmsg_seq = 1,
  },
  .ifi = { .ifi_family = AF_UNSPEC },
 };

 if (send(fd, &req, req.nh.nlmsg_len, 0) < 0) {
  perror("send");
  return 1;
 }

 char buf[16384];
 for (;;) {
  ssize_t len = recv(fd, buf, sizeof(buf), 0);
  if (len < 0) {
   perror("recv");
   return 1;
  }
  for (struct nlmsghdr *nh = (struct nlmsghdr *)buf; NLMSG_OK(nh, len);
       nh = NLMSG_NEXT(nh, len)) {
   if (nh->nlmsg_type == NLMSG_DONE) {
    close(fd);
    return 0;
   }
   if (nh->nlmsg_type == NLMSG_ERROR) {
    fprintf(stderr, "netlink error\n");
    return 1;
   }
   if (nh->nlmsg_type != RTM_NEWLINK)
    continue;

   struct ifinfomsg *ifi = NLMSG_DATA(nh);
   int alen = IFLA_PAYLOAD(nh);
   const char *name = "?";
   struct rtnl_link_stats64 *st = NULL;

   for (struct rtattr *rta = IFLA_RTA(ifi); RTA_OK(rta, alen);
        rta = RTA_NEXT(rta, alen)) {
    if (rta->rta_type == IFLA_IFNAME)
     name = RTA_DATA(rta);
    else if (rta->rta_type == IFLA_STATS64)
     st = RTA_DATA(rta);
   }
   printf("%2d %-12s %s", ifi->ifi_index, name,
          (ifi->ifi_flags & IFF_UP) ? "UP  " : "DOWN");
   if (st)
    printf("  rx %llu pkts  tx %llu pkts",
           (unsigned long long)st->rx_packets,
           (unsigned long long)st->tx_packets);
   printf("\n");
  }
 }
}

