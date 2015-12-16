############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#         Tony Persson, (tony.pesson@rubico.com)
#
############################################################################

STAGING_DIR 	= $(shell pwd)/../staging
CFLAGS		= -c -O0 -g
TARGET		= liblog.a
STAGING_TARGET	= $(STAGING_DIR)/lib/$(TARGET)

CC		= $(CROSS)gcc
LD		= $(CROSS)gcc

all: $(TARGET)

$(TARGET): src/logger.c src/logger.h
	$(CC) $(CFLAGS) src/logger.c
	$(AR) $(ARFLAGS) $(TARGET) logger.o

$(STAGING_TARGET): $(TARGET)
	make force-install

install: $(STAGING_TARGET)

force-install: $(TARGET)
	mkdir -p $(STAGING_DIR)/lib $(STAGING_DIR)/include
	cp liblog.a $(STAGING_DIR)/lib/liblog.a
	cp src/logger.h $(STAGING_DIR)/include

uninstall:
	rm -f $(STAGING_DIR)/lib/liblog.a
	rm -f $(STAGING_DIR)/include/logger.h

clean: 
	rm -f *.[ao]
