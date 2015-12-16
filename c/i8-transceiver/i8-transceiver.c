/*
 * @file   i8-transceiver.c
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * i8-transceiver main file...
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <getopt.h>
#include <string.h>
#include <signal.h>
#include <pthread.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <errno.h>

#include "logger.h"
#include "libipc.h"

#include "packets.h"
#include "test_mode.h"

//#define IEEE
#ifdef IEEE
#include "ieee802154.h"
#endif

/* Defines and macros *********************************************************/

#define TRUE 1
#define FALSE 0

/* Size of packet queue/buffer */
#define PACKET_QUEUE_SIZE (1024 * 1024)

/* Maximum number of nodes in while list / communication list */
#define MAX_NODE_LIST     1024

/* Status report delay in seconds */
#define STATUS_DELAY 60

/* Domain socket buffer sizes */
#define IPC_TX_BUFFER_SIZE (20 * 1024)
#define IPC_RX_BUFFER_SIZE (20 * 1024)

/* Buffer size for "merge fragments payload buffer" */
#define DATA_BUFFER_SIZE (20 * 1024)

/*** Internal data structures *************************************************/

/*
 * Packet queue/buffer structure.
 */
typedef struct queue
{
    uint64_t src;
    packet_t packet;
    time_t   timestamp;
} queue_t;

/*
 * Stats
 */
typedef struct stats
{
    uint32_t total_fragments   ; /* Total number of fragments received */
    uint32_t rejected_fragments; /* Total number of received fragments that was
                                  * rejected due to whitelist. */
} stats_t;

/*** Globals ******************************************************************/

/* i8 still running */
volatile int running = 1;


/*** Internal function protypes ***********************************************/

int main(int argc, char *argv[]);

void sig_handler(int sig);

int setup_ipc_socket(int *fd, struct sockaddr_un *addr);

int setup_test_socket(int *fd, struct sockaddr_in *addr);

#ifdef IEEE
int setup_ieee_socket(int *fd,
		      struct sockaddr_ieee802154 *addr,
		      uint64_t server_addr,
		      uint16_t pan_id);
#endif

int nodelist_add(uint64_t *list, uint64_t new_node, const char *name);

void nodelist_append(uint64_t *target, uint64_t *append, const char *name);

int nodelist_find(uint64_t *list, uint64_t node, const char *name);

int nodelist_count(uint64_t *list);

int build_stats_msg(stats_t *stats,
		    char *data_buffer,
		    size_t *data_buffer_size,
		    uint64_t *whitelist,
		    uint64_t *comlist,
		    time_t timestamp);

int add_to_queue(char *packet_queue,
		 size_t packet_queue_size,
		 packet_t *packet,
		 uint64_t src);

int collect_from_queue(char *packet_queue,
		       size_t packet_queue_size,
		       uint8_t packet_id,
		       uint64_t src,
		       char *data_buffer,
		       size_t *data_buffer_size,
		       time_t *timestamp);

int clean_queue(char *packet_queue, size_t packet_queue_size);

void remove_packet(char *packet_queue,
		   size_t packet_queue_size,
		   uint64_t src,
		   uint8_t packet_id);


int ipc_message_to_bm(int fd,
		      char *data,
		      size_t data_size,
		      char *src,
		      size_t src_size,
		      time_t timestamp);

uint64_t network_to_uint64(uint8_t *addr);

void uint64_to_network(uint64_t in, uint8_t *out);


/*** Functions ****************************************************************/

/*
 * Program entry point.
 *
 * @param argc Argument count. 
 * @param argv Argument vector.
 */
int main(int argc, char *argv[])
{
    ssize_t ret;

#ifdef IEEE
    struct sockaddr_ieee802154 ieee_src_addr;
    struct sockaddr_ieee802154 ieee_addr;
#endif
    struct sockaddr_in test_addr;
    struct sockaddr_in test_src_addr;
    struct sockaddr_un ipc_addr;

    socklen_t ieee_src_addr_len;

    int ieee_fd = 0;  /* IEEE 802.15.4 file descriptor (used as UDP in test mode) */
    int ipc_fd  = 0;  /* Domain/Unix socket file descriptor */

    fd_set read_set;  /* Read flags default */
    fd_set set;       /* Read flags */

    struct timeval timeout; /* Timeout select */
    
    time_t next_status;     /* Time to send next status message */

    pthread_t test_thread; /* Test-mode thread */

    /* Buffer containing packet fragments */
//    static char packet_queue[PACKET_QUEUE_SIZE];
//    size_t packet_queue_size = PACKET_QUEUE_SIZE / sizeof(queue_t);

    char  *packet_queue = NULL;
    size_t packet_queue_size_bytes = PACKET_QUEUE_SIZE;
    size_t packet_queue_size = 0;

    /* Receive buffer for domain socket */
    static char ipc_rx_buf[IPC_RX_BUFFER_SIZE];

    static uint64_t whitelist[MAX_NODE_LIST]; /* Node whitelist */
    static uint64_t comlist[MAX_NODE_LIST];   /* Communicating nodes */

    stats_t stats; /* Containing stats about i8-transceiver */

    int opt = 0;
    int args_ok = TRUE;

    int       test_mode_flag  = 0;    /* Test mode */
    char     *gateway_id      = NULL; /* Gateway id */
    char     *pan_id_str      = NULL; /* IEEE 802.15.4 PANID string*/
    char     *server_addr_str = NULL; /* IEEE 802.15.4 PANID string*/
    uint16_t  pan_id          = 0;    /* IEEE 802.15.4 PANID */
    uint64_t  server_addr     = 0;    /* IEEE 802.15.4 long address */

    /* Get arguments **********************************************************/
    while( ( opt = getopt(argc, argv, "s:g:ta:p:l:") ) != -1)
    {
	switch(opt)
	{
	case 's': /* Receive ieee_buffer size */
	    packet_queue_size_bytes = atoi(optarg) * 1024;
	    break;

	case 'g': /* Gateway id */
	    gateway_id = optarg;
	    break;

	case 't': /* Test mode */
	    test_mode_flag = 1;
	    break;

	case 'a': /* IEEE 802.15.4 long address */
	    server_addr_str = optarg;

	    break;

	case 'p': /* IEEE 802.15.4 PANID */
	    pan_id_str = optarg;

	    break;

	case 'l': /* Log level */
	    if(strcmp(LOG_LEVEL_INFO_STR, optarg) == 0)
		logger_set_level(LOG_INFO);
	    else if(strcmp(LOG_LEVEL_DEBUG_STR, optarg) == 0)
		logger_set_level(LOG_DEBUG);
	    else if(strcmp(LOG_LEVEL_DEV_STR, optarg) == 0)
		logger_set_level(LOG_DEV);
	    else
		args_ok = FALSE;
	    break;

	default:
	    break;
	}
    }

    if( (!args_ok) || (gateway_id == NULL) || (server_addr_str == NULL ) || (pan_id_str == NULL) )
    {
	printf("usage: i8-transceiver -g <gateway id> -a <address> " \
	       "-p <PAN ID> [-s <buffer size [kB]>] [-l <%s|%s|%s>] [-t]\n",
	       LOG_LEVEL_INFO_STR,
	       LOG_LEVEL_DEBUG_STR,
	       LOG_LEVEL_DEV_STR);
	return -1;
    }
	
    server_addr = strtoll(server_addr_str, NULL, 16);
    pan_id = strtoll(pan_id_str, NULL, 16);

    packet_queue = malloc(packet_queue_size_bytes);
    if(packet_queue == NULL)
    {
	ERR("Failed to allocate packet_queue buffer");
	return -1;
    }
    packet_queue_size = packet_queue_size_bytes / sizeof(queue_t);

    signal(SIGINT, sig_handler);

    memset(packet_queue, 0, packet_queue_size * sizeof(queue_t));
    memset(&stats, 0, sizeof(stats_t));
    memset(&whitelist,0, MAX_NODE_LIST * sizeof(uint64_t));
    memset(&comlist, 0, MAX_NODE_LIST * sizeof(uint64_t));

    LOG("i8-transceiver started!");

    /* Start packet generator thread */
    if(test_mode_flag)
    {
        if(pthread_create(&test_thread, NULL, packet_generator, 0))
        {
	    ERR("Test thread: pthread_create: %s", strerror(errno));
	    return -1;
	}

	/* Always whitelist testnode */
	whitelist[0] = TEST_MODE_ADDR;

	LOG("Running in test mode.");
    }

    /*** Setup sockets ********************************************************/

    /* Setup and connect domain socket */
    ret = setup_ipc_socket(&ipc_fd, &ipc_addr);
    if(ret)
    {
	ERR("Failed to setup domain socket");
	return -1;
    }
    LOG("Connected to domain socket");

    if(!test_mode_flag) 
    {
#ifdef IEEE
	/* Setup and bind IEEE 802.15.4 socket */
	ret = setup_ieee_socket(&ieee_fd, &ieee_addr, server_addr, pan_id);
	if(ret)
	{
	    ERR("Failed to setup IEEE 802.15.4 socket");
	    return -1;
	}
	LOG("Bound IEEE 802.15.4 socket.");
#endif
    }
    else
    {
	/* Setup and bind UDP (test) socket */
	ret = setup_test_socket(&ieee_fd, &test_addr);
	if(ret)
	{
	    ERR("Failed to setup UDP (test) socket");
	    return -1;
	}
	LOG("Bound UDP test socket.");
    }

    /* Set masks for select */
    FD_ZERO(&read_set);
    FD_SET(ieee_fd, &read_set);
    FD_SET(ipc_fd, &read_set);
    set = read_set;

    /* Set time for next status message */
    next_status = time(NULL) + STATUS_DELAY;

    /*** Main loop ************************************************************/

    running = TRUE;
    while(running)
    {
	/* Buffer for merging packet.data in */
	static char data_buffer[DATA_BUFFER_SIZE] = {0};

	/* Size of merge buffer */
	size_t data_buffer_size = DATA_BUFFER_SIZE;

	/* Timestamp of messages */
	time_t timestamp = 0;

	/* Timeout for select */
	timeout.tv_sec = 1;
	timeout.tv_usec = 0;

	/* Wait for i8, IPC or timeout (check send status) */
	set = read_set;
	ret = select(FD_SETSIZE, &set, NULL, NULL, &timeout);

	/* Die if select failed. */
	if(ret == -1)
	{
	    ERR("select failed: %s (%d)", strerror(errno), errno);
	    continue;
	}

	/* Received IPC *******************************************************/
	if(FD_ISSET(ipc_fd, &set))
	{
	    int len;
	    static union ipc_msg *msg = (union ipc_msg *) ipc_rx_buf;

            /* Read header */
	    len = recv(ipc_fd, ipc_rx_buf, sizeof(ipc_header_t), 0);
	    if(len < sizeof(ipc_header_t))
	    {
		ERR("Failed to read ipc_header_t from socket (%d bytes read)", len);
		running = FALSE;
		break;
	    }

            /* Saftey check. */
	    if(msg->header.payload_size + sizeof(ipc_header_t) > sizeof(ipc_rx_buf))
	    {
		/* Go home byteport-messenger... You're drunk! */
		ERR("Package from byteport-messenger is bigger than the buffer");
		running = FALSE;
		break;
	    }

            /* Read the rest of the package */
	    len = recv(ipc_fd, ipc_rx_buf + sizeof(ipc_header_t), msg->header.payload_size, 0);
	    if(len != msg->header.payload_size)
	    {
		ERR("Failed to read payload from socket (%d of %d bytes read)", len, msg->header.payload_size);
		running = FALSE;
		break;
	    }

	    DBG("Received %d bytes from byteport-messenger", len);

            /* Handle the package. */
	    switch(msg->header.id)
	    {					
	    case IPC_NODELIST_ID: /* Whitelist */

		DEV("Received whitelist from byteport-messenger:");
		DEV("msg->nodelist.header.id           = %d", msg->nodelist.header.id);
		DEV("msg->nodelist.header.payload_size = %d", msg->nodelist.header.payload_size);
		DEV("msg->nodelist.list_len            = %d", msg->nodelist.list_len);

		if(msg->nodelist.list_len == 0) /* Clean list */
		{
		    memset(whitelist, 0, sizeof(uint64_t) * MAX_NODE_LIST);
		}
		else /* Append to list */
		{
		    nodelist_append(whitelist, msg->nodelist.list, "whitelist");
		}

		/* Temporary whitelist report */
		int i;
		DEV("Whitelist:");
		for(i=0; i<MAX_NODE_LIST; i++)
		{
		    if(whitelist[i] != 0)
			DEV("Whitelist[%02d]: %016llx", i, whitelist[i]);
		    else
			break;
		}

		break;
		
	    case IPC_MESSAGE_ID: /* Message */

		/* TODO: This is where we receive packets/messages that are supposed
                 *       to be sent to nodes.  */

		DEV("Received message from byteport-messenger:");
		DEV("msg->message.header.id           = %d", msg->message.header.id);
		DEV("msg->message.header.payload_size = %d", msg->message.header.payload_size);
		DEV("msg->message.source              = %s", msg->message.source);
		DEV("msg->message.time                = %d", msg->message.time);
		DEV("msg->message.data_len            = %d", msg->message.data_len);
		DEV("msg->message.data                = \"%s\"", msg->message.data);
		break;
	    }
	}

	/* Received IEEE 802.15.4 *********************************************/
	if(FD_ISSET(ieee_fd, &set))
	{
	    int data_received = FALSE;
	    int whitelisted = FALSE;

	    static char ieee_rx_buf[sizeof(packet_t)]; /* Receive buffer */
	    uint64_t src = 0;     /* Address of node */
	    char     src_str[64]; /* Address of node as string */

	    /* Read data from correct socket (depending on testmode or not) */
	    if(!test_mode_flag) /* IEEE 802.15.4 socket */
	    {
#ifdef IEEE
		ieee_src_addr_len = sizeof(struct sockaddr_ieee802154);
		ret = recvfrom(ieee_fd,
			       ieee_rx_buf,
			       sizeof(packet_t),
			       0,
			       (struct sockaddr *) &ieee_src_addr,
			       &ieee_src_addr_len);
		if(ret < 0)
		{
		    ERR("IEEE 802.15.4 socket: recvfrom: %s", strerror(errno));
		    running = FALSE;
		}
		else
		{
		    src = network_to_uint64(ieee_src_addr.addr.hwaddr);
		    stats.total_fragments++;
		    if(nodelist_find(whitelist, src, "whitelist") == 0)
		    {
			/* Node is found in whitelist */
			whitelisted = TRUE;
			data_received = TRUE;
		    }
		    else
		    {
			/* Node was not found in whitelist. */
			whitelisted = FALSE;
			stats.rejected_fragments++;
			nodelist_add(comlist, src, "comlist");
		    }
		}
#endif
	    }
	    else /* Test mode: UDP socket */
	    {
		ieee_src_addr_len = sizeof(struct sockaddr_in);
		ret = recvfrom(ieee_fd,
			       ieee_rx_buf,
			       sizeof(packet_t),
			       0,
			       (struct sockaddr *) &test_src_addr,
			       &ieee_src_addr_len);
		if(ret != sizeof(packet_t))
		{
		    ERR("UDP (test) socket: recvfrom: %s", strerror(errno));
		    running = FALSE;
		}
		else
		{
		    src = TEST_MODE_ADDR;
		    stats.total_fragments++;
		    if(nodelist_find(whitelist, src, "whitelist") == 0)
		    {
			/* Node is found in whitelist */
			whitelisted = TRUE;
			data_received = TRUE;
		    }
		    else
		    {
			/* Node was not found in whitelist. */
			whitelisted = FALSE;
			stats.rejected_fragments++;
			nodelist_add(comlist, src, "comlist");
		    }
		}

	    }

	    /* Parse received data */
	    if( (data_received) && (whitelisted) )
	    {
		packet_t *p = (packet_t *) ieee_rx_buf;
		int ready_to_send = FALSE;

		/* Add something here for future versions */
		if(p->version != PROTO_VER)
		{
		    WARN("Received packet with wrong version (%d != %d)", p->version, PROTO_VER);
		}

		DBG("Received packet: v=%d, ia=%d, ra=%d, "
		    "pid=%d, tsize=%d, off=%d, dsize=%d",
		    p->version,
		    p->is_ack,
		    p->req_ack,
		    p->packet_id,
		    p->total_size,
		    p->offset,
		    p->data_size);

		if(p->is_ack)
		{
		    DEV("Received ack");
		}
		else
		{
		    if(p->total_size > p->data_size) /* Packet is part of a fragmented message! */
		    {
			/* Add packet to receive ieee_buffer */
			add_to_queue(packet_queue,
				     packet_queue_size,
				     p,
				     src);

			/* Was this was the last fragment? */
			if(p->total_size == p->offset + p->data_size)
			{
			    memset(data_buffer, 0, DATA_BUFFER_SIZE);
			    data_buffer_size = DATA_BUFFER_SIZE;
			    timestamp = 0;

			    ret = collect_from_queue(packet_queue,
						     packet_queue_size,
						     p->packet_id,
						     src,
						     data_buffer,
						     &data_buffer_size,
						     &timestamp);
			    if(ret)
			    {
				WARN("Failed to merge packet_id: %d", p->packet_id);
			    }
			    else
			    {
				ready_to_send = TRUE;
			    }
			}
		    }
		    else /* It's not fragmented */
		    {
			memcpy(data_buffer, p->data, p->data_size); 
			data_buffer_size = p->data_size;
			timestamp = time(NULL);
			ready_to_send = TRUE;
		    }

		    /* Send data to byteport-messenger */
		    if(ready_to_send)
		    {
			memset(src_str, 0, 64);
			sprintf(src_str, "%016llx", src);
			ret = ipc_message_to_bm(ipc_fd,
						data_buffer,
						data_buffer_size,
						src_str,
						strlen(src_str),
						timestamp);
			if(ret)
			{
			    WARN("Failed to send packet to byteport-messenger");
			}
		    }
		}

		if(p->req_ack)
		{
		    /* Send an ACK */
		}
	    }

	}

	/* Status report  *****************************************************/
	if(time(NULL) > next_status)
	{
	    DBG("Sending status to byteport-messenger");

	    timestamp = time(NULL);
	    next_status = timestamp + STATUS_DELAY;

	    /* Compose the status message */
	    memset(data_buffer, 0, DATA_BUFFER_SIZE);
	    data_buffer_size = DATA_BUFFER_SIZE;
	    build_stats_msg(&stats,
			    data_buffer,
			    &data_buffer_size,
			    whitelist,
			    comlist,
			    timestamp);

	    /* Send status message to byteport-messenger */
	    ipc_message_to_bm(ipc_fd,
			      data_buffer,
			      data_buffer_size,
			      gateway_id,
			      strlen(gateway_id),
			      timestamp);

	    /* Reset stats */
	    memset(&stats, 0, sizeof(stats_t));
	}
    }	    

    LOG("i8-transceiver shutting down.");

    close(ieee_fd);
    close(ipc_fd);

    if(test_mode_flag)
	pthread_cancel(test_thread);

    pthread_exit(NULL);

    return 0;
}


/*
 * Handle SIGINT...
 *
 * @param sig Signal.
 */
void sig_handler(int sig)
{
    /* Stop! */
    LOG("User abort!");
    running = 0;
}


/*
 * Create and setup IPC socket.
 * 
 * fd   Pointer to file descriptor.
 * addr Poiner to sockaddr_un.
 */
int setup_ipc_socket(int *fd, struct sockaddr_un *addr)
{
    int ret = 0;

    /* Setup IPC socket */
    memset(addr, 0, sizeof(struct sockaddr_un));
    addr->sun_family = AF_UNIX;
    snprintf(addr->sun_path, 108, IPC_SOCKET_PATH);

    /* Create IPC socket */
    *fd = socket(PF_UNIX, SOCK_STREAM, 0);
    if(*fd < 0)
    {
	WARN("Failed to create PF_UNIX socket.");
	return -1;
    }

    /* Connect IPC socket */
    ret = connect(*fd,
		  (struct sockaddr *) addr, 
		  sizeof(struct sockaddr_un));
    if(ret < 0)
    {
	WARN("Could not connect to byteport-messenger");
	return -1;
    }

    return 0;
}

/*
 * Create and setup UDP test socket.
 * 
 * fd   Pointer to file descriptor.
 * addr Poiner to sockaddr_in.
 */
int setup_test_socket(int *fd, struct sockaddr_in *addr)
{
    int ret = 0;

    /* Setup UDP test socket */
    memset(addr, 0, sizeof(struct sockaddr_in));
    addr->sin_family = AF_INET;
    addr->sin_port = htons(TEST_PORT);
    addr->sin_addr.s_addr = htons(INADDR_ANY);

    /* Create UDP test socket */
    *fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if(*fd < 0)
    {
	WARN("Failed to create test-socket: socket: %s", strerror(errno));
	return -1;
    }

    /* Bind UDP test socket */
    ret = bind(*fd, (struct sockaddr *)addr, sizeof(struct sockaddr_in));
    if(ret)
    {
	WARN("Failed to bind test socket: bind: %s", strerror(errno));
	return -1;
    }

    return 0;
}

/*
 * Create and setup IEEE 802.15.4 socket.
 * 
 * fd   Pointer to file descriptor.
 * addr Poiner to sockaddr_ieee802154.
 */
#ifdef IEEE
int setup_ieee_socket(int *fd,
		      struct sockaddr_ieee802154 *addr,
		      uint64_t server_addr,
		      uint16_t pan_id)
{
    int ret;

    /* Setup IEEE 802.15.4 socket */
    memset(addr, 0, sizeof(struct sockaddr_ieee802154));
    addr->family          = AF_IEEE802154;
    addr->addr.addr_type  = IEEE802154_ADDR_LONG;
    addr->addr.pan_id     = pan_id;
    uint64_to_network(server_addr, addr->addr.hwaddr);

    /* Create IEEE 802.15.4 socket */
    *fd = socket(PF_IEEE802154, SOCK_DGRAM, 0);
    if(*fd < 0)
    {
	WARN("Failed to create IEEE 802.15.4: socket: %s", strerror(errno));
	return -1;
    }

    /* Bind IEEE 802.15.4 socket */
    ret = bind(*fd,
	       (struct sockaddr *)addr,
	       sizeof(struct sockaddr_ieee802154));
    if(ret)
    {
	WARN("Failed to bind IEEE 802.15.4 socket: bind: %s", strerror(errno));
	return -1;
    }

    return 0;
}
#endif

/*
 * Add a node to a nodelist.
 *
 * @param list     Pointer to node list.
 * @param new_node New node to add.
 * @param name     String used for LOG-messages.
 *
 * @return  0 if added to list or if already in list,
 *         -1 on fail to add.
 */
int nodelist_add(uint64_t *list, uint64_t new_node, const char *name)
{
    int i;
    int added = FALSE;

    /* See if node already exist in list */
    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(list[i] == new_node)
	    return 0;
    }

    /* Add to list */
    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(list[i] == 0)
	{
	    list[i] = new_node;
	    added = TRUE;
	    break;
	}
    }

    if(added)
    {
	DEV("Node added to %s", name);
	return 0;
    }
    else
    {
	WARN("A %s is full.", name);
	return -1;
    }
}

/*
 * Append to nodelist.
 *
 * Append a "append" nodelist to "target" nodelist.
 *
 * @param target  Target nodelist.
 * @param append  Nodelist to append.
 * @param name    String used for LOG-messages.
 *
 */
void nodelist_append(uint64_t *target, uint64_t *append, const char *name)
{
    int i;
    size_t target_count = 0;
    size_t append_count = 0;

    /* Count target list */
    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(target[i] != 0)
	    target_count++;
	else
	    break;
    }

    /* Count append list */
    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(append[i] != 0)
	    append_count++;
	else
	    break;
    }

    if(target_count + append_count > MAX_NODE_LIST)
    {
	WARN("Can't fit all nodes in %s", name);
	for(i=0; i<MAX_NODE_LIST-target_count; i++)
	    target[i+target_count] = append[i];
    }
    else
    {
	for(i=0; i<append_count; i++)
	    target[i+target_count] = append[i];
    }
}

/*
 * Find a node in nodelist.
 *
 * @param list  Pointer to node list.
 * @param node  Node to find.
 * @param name  String used for LOG-messages.
 *
 * @return  0 if node was found,
 *         -1 if node was NOT found.
 */
int nodelist_find(uint64_t *list, uint64_t node, const char *name)
{
    int i;

    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(list[i] == node)
	    return 0;
    }

    return -1;
}

/*
 * Count nodes in nodelist.
 *
 * @param list  Pointer to node list.
 *
 * @return Number of nodes in nodelist
 */
int nodelist_count(uint64_t *list)
{
    int i;
    int found = 0;

    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(list[i] != 0)
	{
	    found++;
	}
    }

    return found;
}

/*
 * Build status message.
 *
 * Used to prepare the payload in a status message sent to byteport-messenger.
 * 
 * @param stats            Structure containing stats.
 * @param data_buffer      Pointer to data buffer.
 * @param data_buffer_size Total size of data buffer. Will get updated to the
 *                         size of the generated message.
 * @param timestamp        Timestamp of log message.
 */
int build_stats_msg(stats_t *stats,
		    char *data_buffer,
		    size_t *data_buffer_size,
		    uint64_t *whitelist,
		    uint64_t *comlist,
		    time_t timestamp)
{
    int i;
    memset(data_buffer, 0, *data_buffer_size);
    sprintf(data_buffer + strlen(data_buffer), "log|%d|", (int)timestamp);

    sprintf(data_buffer + strlen(data_buffer), "total_received_fragments=%d;", stats->total_fragments);
    sprintf(data_buffer + strlen(data_buffer), "rejected_fragments=%d;", stats->rejected_fragments);

    sprintf(data_buffer + strlen(data_buffer), "nodes_in_whitelist=%d;", nodelist_count(whitelist));
    sprintf(data_buffer + strlen(data_buffer), "nodes_in_comlist=%d;", nodelist_count(comlist));
    sprintf(data_buffer + strlen(data_buffer), "comlist=");

    for(i=0; i<MAX_NODE_LIST; i++)
    {
	if(comlist[i] != 0)
	    sprintf(data_buffer + strlen(data_buffer), "%016llx,", comlist[i]);
    }

    *data_buffer_size = strlen(data_buffer);

    return 0;
}

/*
 * Add a fragment to the packet_queue.
 *
 * Add the packet to first free space in packet_queue. If the packet_queue is full we
 * log a warning message and ...
 *
 * @param  packet_queue      Pointer to packet_queue.
 * @param  packet_queue_size Size of packet_queue
 * @param  packet            Pointer to the packet.
 * @param  src               Address of sending node (binary).
 *
 * @return  0 on success,
           -1 on fail
 */
int add_to_queue(char *packet_queue,
		 size_t packet_queue_size,
		 packet_t *packet,
		 uint64_t src)
{
    int i;
    queue_t *queue_p = NULL;
    int packet_saved = FALSE;

    queue_p = (queue_t *) packet_queue;
    for(i=0; i<packet_queue_size; i++)
    {
	/* Find empty space */
	if(queue_p[i].timestamp == 0)
	{
	    /* Set src address */
	    queue_p[i].src = src;
	    
	    /* Copy packet */
	    memcpy(&queue_p[i].packet, packet, sizeof(packet_t));

	    /* Set time of arrival */
	    queue_p[i].timestamp = time(NULL);

	    packet_saved = TRUE;
	    break;
	}
    }

    if(packet_saved != TRUE)
    {
	WARN("Buffer is full. Removing oldest message.");
	clean_queue(packet_queue, packet_queue_size);
    }
    
    return 0; 
}

/*
 * Collect packet...
 *
 * Takes a packet_id and src address, search through the packet_queue for all
 * the packet fragments, assemble the fragments to a complete message and and 
 * put in data_buffer and update data_buffer_size. The fragments are removed 
 * from the packet_queue.
 *
 * @param  packet_queue      Pointer to packet_queue.
 * @param  packet_queue_size Size of packet_queue
 * @param  packet_id         ID of packet to collect.
 * @param  src               Address of sending node.
 * @param  data_buffer       Buffer to put complete message in.
 * @param  data_buffer_size  Set to the total size of message. Should contain
 *                           buffer length on call.
 * @param  time              Time of first fragment in buffer.
 *
 * @return  0 in success,
 *         -1 on fail.
 */
int collect_from_queue(char *packet_queue,
		       size_t packet_queue_size,
		       uint8_t packet_id,
		       uint64_t src,
		       char *data_buffer,
		       size_t *data_buffer_size,
		       time_t *timestamp)
{
    int i;
    queue_t *queue_p = NULL;
    int bytes_found = 0;

    memset(data_buffer, 0, *data_buffer_size);
    *timestamp = 0;

    /* Find fragments and put into msg data buffer */
    queue_p = (queue_t *) packet_queue;
    for(i=0; i<packet_queue_size; i++)
    {
	/* Check both packet_id and src address */
	if( (queue_p[i].packet.packet_id == packet_id) &&
	    (queue_p[i].src == src) )
	{
	    if(*data_buffer_size < queue_p[i].packet.total_size)
	    {
		ERR("Total packet size is bigger than data_buffer size.");
		return -1;
	    }

	    /* Copy payload data to send buffer */
	    memcpy(data_buffer+queue_p[i].packet.offset,
		   queue_p[i].packet.data,
		   queue_p[i].packet.data_size);

	    /* For sanity check at end */
	    bytes_found += queue_p[i].packet.data_size;

	    /* Set time to first received packet */
	    if(!*timestamp)
		*timestamp = queue_p[i].timestamp;

	    /* Set total size */
	    *data_buffer_size = queue_p[i].packet.total_size;

	    /* Clear message from queue */
	    memset(&queue_p[i], 0, sizeof(queue_t));
	}
    }

    if(bytes_found == *data_buffer_size)
	return 0;
    else
	return -1;
}


/*
 * Clean queue.
 *
 * Search the packet queue for the oldest message and remove all fragments
 * associated to that message.
 *
 * @param packet_queue      Pointer to packet queue.
 * @param packet_queue_size Size of packet queue.
 *
 * @return 
 */
int clean_queue(char *packet_queue, size_t packet_queue_size)
{
    int i;
    queue_t *queue_p;
    time_t   old_timestamp = 2147483647; /* 2038-01-18 (By then we have bigger problems) */
    int      old_index     = -1;
    uint8_t  old_packet_id = 0;
    uint64_t old_src      = 0;

    time_t   timestamp;

    queue_p = (queue_t *) packet_queue;

    /* Find oldest packet in queue */
    for(i=0; i<packet_queue_size; i++)
    {
	timestamp = queue_p[i].timestamp;
	if( (timestamp != 0) && (timestamp < old_timestamp) )
	{
	    old_timestamp = timestamp;
	    old_index     = i;
	}
    }

    old_src = queue_p[old_index].src;
    old_packet_id = queue_p[old_index].packet.packet_id;

    remove_packet(packet_queue, packet_queue_size, old_src, old_packet_id);

    return 0;
}

/*
 * Removes a packet from the packet queue.
 * 
 * Takes a src address and a packet_id and removes all fragmens of the
 * packet from paket_queue. TODO: Could add check that we removed all fragments.
 *
 * @param packet_queue      Pointer to packet queue.
 * @param packet_queue_size Size of packet queue.
 * @param src               Source of packet to remove.
 * @param packet_id         Id of packet to remove.
 *
 */
void remove_packet(char *packet_queue,
		   size_t packet_queue_size,
		   uint64_t src,
		   uint8_t packet_id)
{
    int i;
    int removed = FALSE;
    queue_t *queue_p = NULL;

    queue_p = (queue_t *) packet_queue;
    for(i=0; i<packet_queue_size; i++)
    {
	if( (queue_p[i].src == src) && (queue_p[i].packet.packet_id == packet_id) )
	{
	    memset(&queue_p[i], 0, sizeof(queue_t));
	    removed = TRUE;
	}
    }

    if(!removed)
    {
	ERR("Failed to remove packet from queue");
    }
}

/*
 * Pass on message to byteport-messenger.
 *
 * @param fd         File descriptor to domain socket.
 * @param data       Payload data.
 * @param data_size  Length of payload data.
 * @param src        Sender (gateway_id or ASCII converted node address).
 * @param src_size   Length of sender string.
 * @param time       Timestamp of first received fragment.
 *
 * @return  0 on success,
           -1 on fail.
 */
int ipc_message_to_bm(int fd,
		      char *data,
		      size_t data_size,
		      char *src,
		      size_t src_size,
		      time_t timestamp)
{
    int ret = 0;
    static char ipc_tx_buf[IPC_TX_BUFFER_SIZE];
    union ipc_msg *p = (union ipc_msg *) ipc_tx_buf;

    memset(ipc_tx_buf, 0, IPC_TX_BUFFER_SIZE);    

    p = (union ipc_msg *) ipc_tx_buf;

    /* Set header */
    p->message.header.id = IPC_MESSAGE_ID;
    p->message.header.payload_size = sizeof(char)*64 + sizeof(time_t) + sizeof(uint32_t) + data_size;

    /* Set payload */
    memcpy(p->message.source, src, src_size);  /* Address of node */
    p->message.time      = timestamp;          /* Timestamp */
    p->message.data_len  = data_size;          /* Length of data */
    memcpy(p->message.data, data, data_size);  /* Data from node */
    
#if 1
    /* Temporary debugging */
    DEV("p->message.header.id           = %d", p->message.header.id);
    DEV("p->message.header.payload_size = %d", p->message.header.payload_size);
    DEV("p->message.source              = %s", p->message.source);
    DEV("p->message.time                = %d", p->message.time);
    DEV("p->message.data_len            = %d", p->message.data_len);

    char tmp[32] = {'.'};
    snprintf(tmp, 28, "%s", p->message.data);
    DEV("p->message.data                = \"%s\"", tmp);
#endif

    /* Send packet to domain socket */
    ret = send(fd, ipc_tx_buf, sizeof(ipc_header_t) + p->message.header.payload_size, 0);
    if(ret < 0)
    {
	WARN("Failed to send message to domain socket");
	return -1;
    }
    else
    {
	DBG("Sent message to domain socket (%d bytes)", ret);
    }

    return 0;
}

/*
 * Convert an uint8_t[8] to uint64_t. 
 *
 * Assuming uint8_t[8] has Network/big-endian and we are running on
 * a little-endian machine. TODO: Add endian check and act accordingly.
 *
 * @param addr uint8_t array
 *
 * @return     uint64_t
 */
uint64_t network_to_uint64(uint8_t *addr)
{
    int i;
    uint64_t out = 0;

    for(i=0; i<8; i++)
    {
	/* One of my best lines... EVER */
	out |= (uint64_t) ( (uint64_t) addr[i]<<(56 - 8*i) );
    }

    return out;
    
}

/*
 * Convert an uint64_t to uint8_t[8]. 
 *
 * @param addr uint64_t
 *
 * @return uint8_t array
 */
void uint64_to_network(uint64_t in, uint8_t *out)
{
    int i;

    for(i=0; i<8; i++)
    {
	out[i] = (uint8_t) ( 0xFF & (in>>(56 - 8*i)) );
    }
}

