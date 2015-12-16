############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#
############################################################################

STAGING_DIR	= ../libs/staging
TARGET		= byteport-stomp-client
CFLAGS		= -Wall -O0 -g -c -I$(STAGING_DIR)/include -I$(STAGING_DIR)/include/apr-1 -D_LARGEFILE64_SOURCE
LDFLAGS		= -L$(STAGING_DIR)/lib -lstomp -lapr-1 -llog
OBJS		= byteport-stomp-client.o

CC		= $(CROSS)gcc
LD		= $(CROSS)gcc

all: libs $(TARGET) i8_fake_client

libs:
	@make -C ../libs

$(TARGET): $(OBJS) $(STAGING_DIR)/lib/libstomp.a $(STAGING_DIR)/lib/libapr-1.a $(STAGING_DIR)/lib/liblog.a
	$(LD) $(OBJS) $(LDFLAGS) -o $(TARGET)

i8_fake_client: i8_fake_client.c
	gcc -O0 -g -I$(STAGING_DIR)/include i8_fake_client.c -o i8_fake_client

test: all
	./byteport-stomp-client -l debug -g robban-gw-0 -q /queue/simple_string_dev_message -n rubicodev -s broker.byteport.se -p 61613 -d

bomb: all
	cp ./byteport-stomp-client bomber
	./bomber -g robban-gw-0 -q /queue/device_messages_rubicodev.robban-gw-0 -n rubicodev -s broker.byteport.se -p 61613 -b 100 -r 10

stop:
	killall bomber

gdb: all
	gdb -x .gdbinit --args ./byteport-stomp-client -l debug -g robban-gw-0 -q /queue/simple_string_dev_message -n rubicodev -s broker.byteport.se -p 61613 -d
	
valgrind: all
	valgrind --leak-check=full --show-reachable=yes ./byteport-stomp-client -l debug -g robban-gw-0 -q /queue/simple_string_dev_message -n rubicodev -s broker.byteport.se -p 61613 -d

clean:
	rm -f $(TARGET) $(OBJS) i8_fake_client bomber
