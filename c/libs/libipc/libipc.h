/*
 * @file   libipc.h
 * @author Tony Persson (tony.persson@rubico.com)
 *
 * Message format for inter-process communication between byteport-messenger
 * and i8-transceiver.
 */

#ifndef _LIBIPC_H_
#define _LIBIPC_H_

#include <stdint.h>
#include <time.h>

/* Path to domain socket for inter-process communication */
#define IPC_SOCKET_PATH "/tmp/bpm-ipc"

/* IPC message ID number */
enum {
	IPC_NODELIST_ID,
	IPC_MESSAGE_ID,
};

/*
 * Header of all packages.
 */ 
typedef struct ipc_header
{
    uint32_t id;            /* ID to identify packet in IPC-communication */
    uint32_t payload_size;  /* Number of bytes in the package after the header. */
} ipc_header_t;

/*
 * List of nodes. 
 *
 * i8 -> bm: List of communicating nodes.
 * bm -> i8: Whitelist of nodes.
 */
typedef struct ipc_nodelist
{
    ipc_header_t header;    
    uint16_t     list_len; /* Number of nodes in list */
    uint64_t     list[1];  /* List of nodes */
} ipc_nodelist_t;

/*
 * Message sent to or from a node. Direction depending on sender.
 */
typedef struct ipc_message
{
    ipc_header_t header;    
    char         source[64]; /* Id string of node */
    time_t       time;       /* Timestamp (only for received packets) */
    uint32_t     data_len;   /* Length of data */
    char         data[1];    /* Data */
} ipc_message_t;


union ipc_msg
{
    ipc_header_t   header;
    ipc_nodelist_t nodelist;
    ipc_message_t  message;
};

#endif
