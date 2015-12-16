############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#
############################################################################

APR_FILE    		= apr-1.4.6.tar.gz
APR_DIR     		= apr-1.4.6
TARGET      		= $(APR_DIR)/.libs/libapr-1.a
STAGING_TARGET_DIR	= $(STAGING_DIR)/include/apr-1
STAGING_DIR 		= $(shell pwd)/../staging

CC			= $(CROSS)gcc
LD			= $(CROSS)gcc

all: $(TARGET)

$(TARGET):  
	rm -rf $(APR_DIR)
	tar xfvz $(APR_FILE)
	cd $(APR_DIR) && ./configure --prefix=$(STAGING_DIR)
	make -C $(APR_DIR)

$(STAGING_TARGET_DIR):
	make force-install

install: $(STAGING_TARGET_DIR)

force-install: $(TARGET)
	make -C $(APR_DIR) install
	cp -a $(APR_DIR)/include/arch $(STAGING_TARGET_DIR)
	
clean:
	rm -rf $(APR_DIR)
