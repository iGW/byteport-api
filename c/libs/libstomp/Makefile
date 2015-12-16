############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#
############################################################################

STAGING_DIR 	= $(shell pwd)/../staging
INCLUDE_DIR	= $(STAGING_DIR)/include/apr-1
CFLAGS		= -O0 -g -c -I $(INCLUDE_DIR)
TARGET		= stomp.a
STAGING_TARGET	= $(STAGING_DIR)/lib/$(TARGET)

CC		= $(CROSS)gcc
LD		= $(CROSS)gcc

all: $(TARGET)

$(TARGET): stomp.o Makefile
	$(AR) $(ARFLAGS) $(TARGET) stomp.o

%.o : src/%.c
	$(CC) $(CFLAGS) $< -o $@

$(STAGING_TARGET): $(TARGET)
	make force-install

install: $(STAGING_TARGET)

force-install: $(TARGET)
	mkdir -p $(STAGING_DIR)/lib $(STAGING_DIR)/include
	cp stomp.a $(STAGING_DIR)/lib/libstomp.a
	cp src/stomp.h $(STAGING_DIR)/include

uninstall:
	rm -f $(STAGING_DIR)/lib/libstomp.a
	rm -f $(STAGING_DIR)/include/stomp.h

clean: 
	rm -f *.[ao]
