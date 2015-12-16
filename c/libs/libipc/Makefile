############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#         Tony Persson, (tony.pesson@rubico.com)
#
############################################################################

STAGING_DIR 	= $(shell pwd)/../staging
TARGET		= $(STAGING_DIR)/include/libipc.h

install: $(TARGET)

force-install: install

$(TARGET): libipc.h
	mkdir -p $(STAGING_DIR)/include
	cp ./libipc.h $(STAGING_DIR)/include

uninstall:
	rm -f $(STAGING_DIR)/include/libipc.h

clean: 
