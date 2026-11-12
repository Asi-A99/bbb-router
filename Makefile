PREFIX ?= /usr

all: bbr-links

bbr-links: tools/bbr-links.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -Wall -Wextra -o $@ $<

install: bbr-links
	install -D -m 0755 bbr-links $(DESTDIR)$(PREFIX)/bin/bbr-links

clean:
	 rm -f bbr-links

