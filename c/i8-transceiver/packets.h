/*
 * @file   packets.h
 * @author Tony Persson (tony.persson@rubico.com)
 * 
 * Defines the packets between Gateway and nodes.
 */

#ifndef _PACKETS_H_
#define _PACKETS_H_

#include <stdint.h>

/* Size of payload from IEEE 802.15.4 frame */
#define PAYLOAD_SIZE 80

/* Maximum value of fragment_total */
#define MAX_FRAGMENT_TOTAL 0xFF

/* Protocol version */
#define PROTO_VER 1

/*
 * Basic packet structure.
 */
typedef struct __attribute__ ((__packed__)) packet
{
    /* Flags */
    uint8_t  version:3;           /**< Protocol version. */
    uint8_t  req_ack:1;           /**< ACK is requested. */
    uint8_t  is_ack:1;            /**< Packet is ACK. */
    uint8_t  reserved:3;          /**< Reserved bits */

    uint8_t  packet_id;           /**< Packet ID. Used for ACK-req and ACKs. */
    uint32_t total_size;          /**< Total amount of data in message. */
    uint32_t offset;              /**< Offset to first byte. */
    uint8_t  data_size;           /**< Size of data in packet */
    char     data[PAYLOAD_SIZE];  /**< Data */
} packet_t;

#endif
