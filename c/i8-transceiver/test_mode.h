/*
 * @file   test_mode.h
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * Creates a socket and generates fake packets for i8-tranceiver.
 */

#ifndef _TEST_MODE_H_
#define _TEST_MODE_H_

/* Port for UDP test traffic */
#define TEST_PORT 12000

/* Address used by test_mode */
#define TEST_SERVER "localhost"

/* Fake 802.15.4 long address of test node */
#define TEST_MODE_ADDR 0x0102030405060708

void *packet_generator(void *arg);

#endif
