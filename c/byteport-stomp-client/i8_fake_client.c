#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <fcntl.h>
#include <libipc.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/select.h>

#define MIN(a, b) (((a) < (b)) ? (a) : (b))

int main(void)
{
	int s, len, done;
	struct sockaddr_un remote;
	static char buffer[10*1024];
	char *x = "|/-\\";
	int xi = 0;

	for(;;)
	{
		if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) 
		{
			perror("socket");
			exit(1);
		}

		printf("Trying to connect... %c\r", x[xi++ & 3]);
		fflush(stdout);

		remote.sun_family = AF_UNIX;
		strcpy(remote.sun_path, IPC_SOCKET_PATH);
		len = strlen(remote.sun_path) + sizeof(remote.sun_family);
		if (connect(s, (struct sockaddr *)&remote, len) == -1) 
		{
			
			close(s);
			sleep(1);
			continue;
		}

		printf("\nConnected.\n");
		printf("> ");
		
		done = 0;
		while(!done)
		{
			fd_set read_set;
			int n;
			struct timeval tv;
			char *x ="|/-\\";
			static int xi = 0;
			
			FD_ZERO(&read_set);
			FD_SET(0, &read_set);
			FD_SET(s, &read_set);

			tv.tv_sec = 0;
			tv.tv_usec = 100000;
			n = select(FD_SETSIZE, &read_set, NULL, NULL, &tv);
			
			// Restart the loop if select failed.
			if(n == -1)
			{
				printf("select failed: %s (%d)\n", strerror(errno), errno);
				continue;
			}
			
			// Restart the loop if select timed out.
			if(n == 0)
			{
				fprintf(stderr, "%c\b", x[(xi++)& 3]);
				continue;
			}

			if(FD_ISSET(0, &read_set))
			{
				fgets(buffer, 100, stdin);
				printf("> ");
				
				// Nodelist
				if(strcmp(buffer, "n\n") == 0)
				{
					ipc_nodelist_t *nodelist = (ipc_nodelist_t *)buffer;
					int i;
					
					nodelist->header.id = IPC_NODELIST_ID;
					nodelist->list_len = 32;
					nodelist->header.payload_size = sizeof(ipc_nodelist_t) - sizeof(ipc_header_t) + sizeof(uint64_t) * (nodelist->list_len - 1);
					for(i = 0; i < nodelist->list_len; i++)
						nodelist->list[i] = i;

					send(s, buffer, nodelist->header.payload_size + sizeof(ipc_header_t), 0);
				}
				
				// Message
				if(strcmp(buffer, "m\n") == 0)
				{
					ipc_message_t *message = (ipc_message_t *)buffer;
					message->header.id = IPC_MESSAGE_ID;
					snprintf(message->source, sizeof(message->source), "My Sensor");
					message->time = 1234567890;
					snprintf(message->data, 20, "Hej på dig!");
					message->data_len = strlen(message->data);
					message->header.payload_size = sizeof(ipc_message_t) - sizeof(ipc_header_t) - 1 + message->data_len;
					send(s, buffer, message->header.payload_size + sizeof(ipc_header_t), 0);
				}
			}

			if(FD_ISSET(s, &read_set))
			{
				ipc_header_t *header = (ipc_header_t *)buffer;
				if(recv(s, buffer, sizeof(ipc_header_t), 0) <= 0)
				{
					done = 1;
					break;
				}
				
				if(header->id == IPC_MESSAGE_ID)
				{
					ipc_message_t *message = (ipc_message_t *)buffer;
					printf("message->header.payload_size = %d\n", message->header.payload_size);
					recv(s, buffer + sizeof(ipc_header_t), message->header.payload_size, 0);

					printf("Source=[%s], time=%d, data_len=%d, data=[%s]\n", message->source, (int)message->time, message->data_len, message->data);
				}
				
				if(header->id == IPC_NODELIST_ID)
				{
					int i;
					ipc_nodelist_t *nodelist = (ipc_nodelist_t *)buffer;
					printf("nodelist->header.payload_size = %d\n", nodelist->header.payload_size);
					
					if(nodelist->header.payload_size + sizeof(ipc_header_t) > sizeof(buffer))
					{
						int n;
						printf("ERROR: payload to big\n");
						
						while(nodelist->header.payload_size)
						{
							n = nodelist->header.payload_size;
							n = MIN(sizeof(buffer), nodelist->header.payload_size);
							nodelist->header.payload_size -= n;
							recv(s, buffer, n, 0);
						};
					} else {
						recv(s, buffer + sizeof(ipc_header_t), nodelist->header.payload_size, 0);

						printf("list_len = %d\n", nodelist->list_len);
						if(nodelist->list_len == 0)
							printf("Clearing whitelist\n");
						else
							printf("Adding to whitelist:\n");

						for(i = 0; i < nodelist->list_len; i++)
							printf("node (%d): 0x%llx\n", i, (long long unsigned int)nodelist->list[i]);
					}
				}
			}	
		}

		close(s);
	}
	
	return 0;
}
