############################################################################
#
# Copyright (c) 2013, Rubico AB (www.rubico.com)
#
# Author: Robert Selberg, (robert.selberg@rubico.com)
#         Tony Persson, (tony.persson@rubico.com)
#
############################################################################

TARGET		= i8-transceiver
CFLAGS		= -g -c -I../libs/staging/include -Wall
LDFLAGS		= -L../libs/staging/lib -llog -lpthread
#OBJS		= $(subst .c,.o,$(shell ls *.c))
OBJS            = i8-transceiver.o test_mode.o

CC			= $(CROSS)gcc
LD			= $(CROSS)gcc

all: $(TARGET)

$(TARGET): $(OBJS)
	$(LD) $(OBJS) $(LDFLAGS) -o $(TARGET)

test: all
	./i8-transceiver -l DEV -t -g tony-gw-0 -p 1234 -a 1234567812345678

clean:
	rm -f $(TARGET) $(OBJS)
