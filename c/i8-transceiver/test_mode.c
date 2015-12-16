/*
 * @file   test_mode.c
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * Creates a socket and generates fake packets for i8-tranceiver.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <pthread.h>

#include "test_mode.h"
#include "packets.h"
#include "logger.h"

/* Running variable defined and set in i8-transceiver.c */
extern int running;

/* Test messages */

static char msg[] = "lt_af1|K2,M2,A3,T125";
/*
static char msg_log[] = "log|1362041799|This planet has — or rather had — a problem, which was \
this: most of the people living on it were unhappy for pretty much all of the \
time. Many solutions were suggested for this problem, but most of these were \
largely concerned with the movement of small green pieces of paper, which was \
odd because on the whole it wasn't the small green pieces of paper that were \
unhappy.";
*/
/* Internal function prototypes */
void send_message(char *str,
		  uint8_t packet_id,
		  int fd,
		  struct sockaddr_in *i8_addr);

ssize_t send_packet(char *data,
		    size_t data_size,
		    uint8_t packet_id,
		    uint32_t total_size,
		    uint32_t offset,
		    int fd,
		    struct sockaddr_in *i8_addr);


/*
 * Creates a test socket (UDP in this case) and simulate nodes sending
 * packets to i8-transeiver.
 */
void *packet_generator(void *arg)
{
    struct sockaddr_in i8_addr;

    int i8_fd;
    int ret;

    int packet_id = 0;

    /* Create socket */
    i8_fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if(i8_fd < 0)
    {
	ERR("Fake node: Failed to create socket.");
    }

    /* Setup socket */
    memset(&i8_addr, 0, sizeof(struct sockaddr_in));
    i8_addr.sin_family = AF_INET;
    i8_addr.sin_port = htons(TEST_PORT);
    ret = inet_aton(TEST_SERVER, &i8_addr.sin_addr);
    if(ret < 0)
    {
	ERR("Fake node: Failed to setup socket.");
    }

    sleep(1);

    packet_id = 0;
    while(running)
    {
	send_message(msg, packet_id, i8_fd, &i8_addr);
	packet_id++;
	sleep(5);
    }

    close(i8_fd);

    DEV("Fake node: Thread exiting");

    pthread_exit(NULL);
}

/*
 * Send a test message.
 *
 * Calculate number of fragments needed to send message and call send_packet
 * tot_frags number of times.
 * 
 * @param str        Message to send.
 * @param packet_id  The packet ID.
 * @param fd         Socket file descriptor.
 * @param i8_addr    Socket address structure.
 */
void send_message(char *str, uint8_t packet_id, int fd, struct sockaddr_in *i8_addr)
{
    size_t total_size;   /* Total length of message. */
    size_t pkt_size;     /* Length of payload in packet */
    int    offset;       /* Offset */
    int    frag_no;
    int    tot_frags;

    total_size = strlen(str) + 1;
    
    DEV("Fake node: Sending message (packet_id=%d, total_size=%d)",
	packet_id, total_size);
    
    tot_frags = total_size / PAYLOAD_SIZE;

    for(frag_no=0; frag_no<=tot_frags; frag_no++)
    {
	if(frag_no == tot_frags)
	    pkt_size = total_size % PAYLOAD_SIZE;
	else
	    pkt_size = PAYLOAD_SIZE;

	offset = frag_no * PAYLOAD_SIZE;
	send_packet(str,
		    pkt_size,
		    packet_id,
		    total_size,
		    offset,
		    fd,
		    i8_addr);
    }
}

/*
 * Populate and send packet.
 *
 * @param 
 * @param 
 * @param 
 * @param 
 * @param 
 */
ssize_t send_packet(char *data,
		    size_t data_size,
		    uint8_t packet_id,
		    uint32_t total_size,
		    uint32_t offset,
		    int fd,
		    struct sockaddr_in *i8_addr)
{
    ssize_t ret = 0;
    socklen_t i8_addr_len;
    packet_t p = {0};
    memset(&p, 0, sizeof(packet_t));

    /* Static in alpha version */
    p.version        = 0x1;  /**< Protocol version. */
    p.req_ack        = 0;    /**< ACK is requested. */
    p.is_ack         = 0;    /**< Packet is ACK. */
    p.reserved       = 0;    /**< Reserved bits */

    p.packet_id      = packet_id;
    p.total_size     = total_size;
    p.offset         = offset;
    p.data_size      = data_size;

    memcpy(p.data, data + offset, data_size);
    
    i8_addr_len = sizeof(struct sockaddr_in);
    ret = sendto(fd, &p, sizeof(packet_t), 0, (struct sockaddr *) i8_addr, i8_addr_len);

    if(ret < 0)
	ERR("Fake node: Failed to send a packet");

    return ret;
}

