obj-m += bbr_count.o
KDIR ?= $(HOME)/Desktop/YOCTO/bbb-router/linux
ARCH ?= arm
CROSS_COMPILE ?= arm-linux-gnueabihf-

all:
	 $(MAKE) -C $(KDIR) M=$(CURDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) modules
clean:
	 $(MAKE) -C $(KDIR) M=$(CURDIR) clean

