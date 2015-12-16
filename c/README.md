# C Implementation of the Byteport-APIs

This directory contains a number of components built for a project where a number of sensors
communicating over a IEEE802.15.4 network needed to send data to Byteport.

## Directories:
 /byteport-stomp-client
  C implementation of the STOMP client connecting to the Byteport RABBITMQ message broker (up and down).
  
 /i8-transceiver  
  This program acts as a bridge between a ieee802.15.4 network and the Byteport STOMP client.
 
 /libs/apr
  ?
 
 /libs/libipc
  Packet definitions for the integrating with the byteport-stomp-client
  
 /libs/liblog
  Shared library used to log data to log server.
  
 /libs/libstomp
  C implementation of the STOMP protocol, see also /lib/libstomp/README.txt
  
  
## TODO
 - SSL encryption for STOMP client. 
 - HTTP/HTTPS client implementation.
