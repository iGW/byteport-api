############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#
############################################################################

LIBS = apr libstomp liblog libipc
STAGING_DIR = staging

all:
	for lib in $(LIBS); do make -C $$lib install || exit 1; done
		
clean:
	for lib in $(LIBS); do make -C $$lib clean || exit 1; done
	rm -rf $(STAGING_DIR)
