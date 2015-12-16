 /**
 * @file byteport-messenger.c
 * @author Robert Selberg, Rubico AB (2013).
 *
 * @description TODO fix endian in this file.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stomp.h>
#include <arch/unix/apr_arch_networkio.h>
#include <logger.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>
#include <string.h>
#include <fcntl.h>
#include <libipc.h>

// #define USERNAME ""
// #define PASSWORD ""

#define MAX_STOMP_PACKAGE_SIZE (20*1024)
#define MAX_I8_PACKAGE_SIZE (20*1024)
#define GS_DATA_POOL_SIZE (20*1024)
#define SUBSCRIBE_QUEUE_PREFIX "/queue/device_messages_"

#define APR_ERROR_EXIT(str, reason)	apr_error_exit(__FILE__, __LINE__, str, reason)
#define APR_ERROR(str, reason)		apr_error(__FILE__, __LINE__, str, reason)

#define ARRAY_LENGTH(array) (sizeof(array) / sizeof(array[0]))
#define MIN(a, b) (((a) < (b)) ? (a) : (b))

#ifdef __APPLE__
#define MSG_NOSIGNAL 0
#endif

//const char *gs_str = "lajskflashjkflhasdfgasdjfgawjfbjw4gfvuiasdgcwr7iufgentljhvfbsdjklhq37i5ohtl3hf7834hnfvbguy24gr3kgfuiqwfgq3uk46fi8wFGUIQ4TFO34TF8WOYFG34LFGHVO35GHHQ357OGYQ385YGHQEIVGICTBFR9XYNQ3IFQUXIDY298ROFQ3NTXIFH24HX8FQN8TWXEGF284OTRGFUIQ34GCJK2GFTFGUGFJKSEgfGEUIFGEihuifgjk3g5uyebvyl34gfvgb3yvgey5lhgyvwg54egvkbasfdgaei5ofgbajksdfgvuiaerfbkq35hgvuiasfvbsejk5ygheg5ogvbeuiyvhiastvuiasdtv78asdftv5asduyfvtasd7vr5D7FRSD78FTQ7CTIQ4CNTW35Q789FHQW4IFTGQWEFYQB4CFHAWD8OIFBAWKEUFGASEUKGCFAUKS6GCFKAWUE7FGIL2AÖRGHLAEHFKLSETHGPAERYGFVKQ2K4I7FTGAWRILFGAWOIEFGKQWY6FOQ7IWYDFNOXBN24RXDTB92QXM8TXFYOQ4FYQW34CGAWIOYHFQ8O4YRGO2TGQF6Q2TGGVQIF4Q23KLAJSDHFIASDY7FOWLfbgasdfy70awo4yfg3ioaeygvbaolfgaw7pofgawylirfgae0gyhq3yi5ogvoaeirufg8oyvq384ow74yfgoqw4yfiqwp4hf7ioq34yhfipqw4yhfilgvqwrcgvbawydaseuifhDFGYF6W47TF89F5W6etfaehfq27i4ohfqlwFGUasdgfawuotfigwefgaweitgfbwu4tfgoEIABFQW7OTRFQ2GRF8Q4WYEDOQWUIOETFYG264OYFBQ0943GPFPQW04FGHPQWG48FY0QWP4OFH6G";

typedef int BOOL;

enum
{
	MODE_UNKNOWN,
	MODE_SEND_MESSAGE,
	MODE_BOMBER,
	MODE_DAEMON,
};

static volatile BOOL gs_die = FALSE;

static char input_buffer[MAX_I8_PACKAGE_SIZE];
static char output_buffer[MAX_STOMP_PACKAGE_SIZE];

/*
 * The gs_data-stuff below is a small pool for allocating memory that is used only for a very short time. 
 * There is no free function. The only way to free memory is t call gs_data_init() to re-initialize the poool.
 * All the gs_data_init function do is setting the index to zero..
 * 
 */ 
static char gs_data[GS_DATA_POOL_SIZE];
static int gs_data_index = 0;

// Initialize the gs_data pool.
static void gs_data_init()
{
	gs_data_index = 0;
	bzero(gs_data, sizeof(gs_data));
}

// Allocate data from the gs_data pool.
static void *gs_data_alloc(size_t size)
{
	if(gs_data_index + size < sizeof(gs_data))
	{
		gs_data_index += size;
		return &gs_data[gs_data_index - size];
	} else {
		ERR("gs_data size to small!");
		return NULL;
	}
}

// Called when a critical error is retruned from the APR functions.
static void apr_error(char* file, int line, char *str, apr_status_t reason)
{
	char buffer[80];
	apr_strerror(reason, buffer, sizeof(buffer));
	logger(file, line, LOG_ERROR, "%s: %s (%d)", str, buffer, reason);
}

static void apr_error_exit(char* file, int line, char *str, apr_status_t reason)
{
	apr_error(file, line, str, reason);
	exit(-1);
}

void signal_handler(int sig)
{
	fprintf(stderr, "Received signal: %d\n", sig);
	gs_die = TRUE;
}

// Disconnects a stomp connection.
static void bm_disconnect(stomp_connection **connection)
{
	apr_status_t rc = stomp_disconnect(connection);
	if(rc != APR_SUCCESS)
		APR_ERROR_EXIT("stomp_disconnect failed", rc);
}

// Connects to a stomp server.
static void bm_connect(stomp_connection **connection, apr_pool_t *pool, char *server_string, unsigned int port)
{
	apr_status_t rc;
	stomp_frame wframe;
	stomp_frame *rframe = NULL;

	for(;;)
	{
		// Establish the Stomp Connection
		LOG("Connecting to %s:%d", server_string, port);
		rc = stomp_connect(connection, server_string, port, pool);
		if(rc != APR_SUCCESS)
		{
			APR_ERROR("stomp_connect failed", rc);
			LOG("Waiting 10 seconds...");
			sleep(10);
			continue;
		}

		// Send CONNECT frame
		bzero(&wframe, sizeof(wframe));
		wframe.command = "CONNECT";
#ifdef USERNAME
		wframe.headers = apr_hash_make(pool);
		apr_hash_set(wframe.headers, "login", APR_HASH_KEY_STRING, USERNAME);
		apr_hash_set(wframe.headers, "passcode", APR_HASH_KEY_STRING, PASSWORD);
#endif
		rc = stomp_write(*connection, &wframe, pool);
		if(rc != APR_SUCCESS)
		{
			APR_ERROR("stomp_write failed", rc);
			bm_disconnect(connection);
			continue;
		}


		// Read a frame
		rc = stomp_read(*connection, &rframe, pool);
		if(rc != APR_SUCCESS)
		{
			APR_ERROR("connection", rc);
			bm_disconnect(connection);
			continue;
		}		

		LOG("Response: %s", rframe->command);
		break;
	}
}

/*
 * @description This function parses a json message and fills a struct with the info.
 * @param field_name is the name of the field. In the example below it can be either uid or data.
 * @param struct_array_base is a pointer to a struct array with char * members. I.e: struct { char *uid; char *data; }
 * @param struct_member_offset is the offset of the member in the struct. In the exapel above "char *uid" is 0, and "char *data" is 1.
 * @param number_of_struct_members is the total number of members in the struct. 2 in the example above.
 * @param max_number_of_array_entries is the max number of entries the array can hold.
 * @param json_message the a null terminated string to parse.
 * 
 * Example of json_message:
 * 
 * [{ 
 *   "uid": "127",
 *   "data": "cmd_reboot=1;"
 * },
 * { 
 *   "uid": "127",
 *   "data": "cmd_reboot=1;"
 * }]
 */

static int get_json_value_by_field(char *field_name, void *struct_array_base, unsigned int struct_member_offset, size_t number_of_struct_members, int max_number_of_array_entries, char *json_message)
{
	char buffer[100];
	char *p, *p_start, *dst;
	int i;
	
	for(i = 0; i < max_number_of_array_entries; i++)
	{
		// Create a buffer with i.e. "uid".
		snprintf(buffer, sizeof(buffer), "\"%s\"", field_name);
		
		// Search for "uid" in json_message.
		p = strstr(json_message, buffer);
		if(p == NULL)
			break;
		
		// Jump over "uid" and search for the next " token.
		json_message = p + strlen(buffer);
		p = strchr(json_message, '"');
		if(p == NULL)
			break;

		// Jump over it
		p++;

		// Save a pointer to the argument
		p_start = p;

		// Search for the ending " token ...
		p = strchr(p, '"');
		if(p == NULL)
			break;

		// Copy the argument to the gs_data array and set the pointer in the structure.
		dst = gs_data_alloc(p - p_start + 1);
		*((char **)struct_array_base + struct_member_offset + number_of_struct_members * i) = dst;
		strncpy(dst, p_start, p - p_start);
   
		
		json_message = p + 1;
		if(*json_message == 0)
			break;
	}

	return i;
}

/*
 * @returns FALSE if there is something wrong with any connection.
 */
static BOOL receive_from_i8(int i8_connection, stomp_connection *write_connection, char *write_queue, char *namespace, char *gateway_id, apr_pool_t *pool)
{
	int len;
	const ipc_header_t *header = (ipc_header_t *)input_buffer;

	// Read header
	len = recv(i8_connection, input_buffer, sizeof(ipc_header_t), 0);
	if(len != sizeof(ipc_header_t))
	{
		ERR("Failed to read ipc_header_t from socket (%d bytes read)", len);
		return FALSE;
	}

	// Saftey check.
	if(header->payload_size + sizeof(ipc_header_t) > sizeof(input_buffer))
	{
		ERR("Package from i8 tranceiver is bigger than the input_buffer");
		return FALSE;
	}

	// Read the rest of the package
	len = recv(i8_connection, input_buffer + sizeof(ipc_header_t), header->payload_size, 0);
	if(len != header->payload_size)
	{
		ERR("Failed to read payload from socket (%d of %d bytes read)", len, header->payload_size);
		return FALSE;
	}

	LOG("Received %d bytes from i8 tranceiver", len);

	// Handle the package.
	switch(header->id)
	{					
		apr_status_t rc;
		stomp_frame frame;

		// Handle the unknown nodes list
		case IPC_NODELIST_ID: 
		{					
			int i, j, step_size = 16;
			const ipc_nodelist_t *nodelist = (ipc_nodelist_t *)input_buffer;

			LOG("Sending nodelist to stomp server");
			
			// Loop through all entries in the list
			for(i = 0; i < nodelist->list_len; i += step_size)
			{
				char str[1024];
				int len;

				snprintf(str, sizeof(str), "{");

				// Build small text strings to send to the server.
				for(j = 0; j < step_size && i < nodelist->list_len; j++)
				{
					len = strlen(str);
					snprintf(str + len, sizeof(str) - len, "%s0x%llx", (j == 0) ? "" : ", ", nodelist->list[i + j]);
				} 

				len = strlen(str);
				snprintf(str + len, sizeof(str) - len, "}");
				
				bzero(&frame, sizeof(frame));
				frame.command = "SEND";
				frame.headers = apr_hash_make(pool);
				apr_hash_set(frame.headers, "destination", APR_HASH_KEY_STRING, write_queue);
				apr_hash_set(frame.headers, "content-type", APR_HASH_KEY_STRING, "text/plain");
				snprintf(output_buffer, sizeof(output_buffer), "[{\"data\": \"%s\", \"namespace\": \"%s\", \"uid\": \"%s\"}]", str, namespace, gateway_id);
				frame.body = output_buffer;
				frame.body_length = strlen(frame.body);

				DBG("frame.body_length = %d, frame.body = [%s]", frame.body_length, frame.body);

				rc = stomp_write(write_connection, &frame, pool);
				if(rc != APR_SUCCESS)
				{
					APR_ERROR("stomp_write failed", rc);
					return FALSE;
				}
			}

			break;
		}
			
		// Handle normal messages
		case IPC_MESSAGE_ID:
		{
			ipc_message_t *message = (ipc_message_t *)input_buffer;

			LOG("Sending message to stomp server");

			bzero(output_buffer, sizeof(output_buffer));
			snprintf(output_buffer, sizeof(output_buffer) - 1, "[{ \"uid\": \"%s\", \"namespace\": \"%s\", \"data\": \"%s\", \"timestamp\": \"%llu\" }]", message->source, namespace, message->data, (unsigned long long)message->time);

			bzero(&frame, sizeof(frame));
			frame.command = "SEND";
			frame.headers = apr_hash_make(pool);
			apr_hash_set(frame.headers, "destination", APR_HASH_KEY_STRING, write_queue);
			apr_hash_set(frame.headers, "content-type", APR_HASH_KEY_STRING, "text/plain");
			frame.body = output_buffer;
			frame.body_length = strlen(frame.body);

			DBG("frame.body_length = %d, frame.body = [%s]", frame.body_length, frame.body);

			rc = stomp_write(write_connection, &frame, pool);
			if(rc != APR_SUCCESS)
			{
				APR_ERROR("stomp_write failed", rc);
				return FALSE;
			}

			break;
		}
	}
	
	return TRUE;
}

/*
 * @param i8_connection is a filedescriptor.
 * @param data is a null terminated string with comma separated values: "0x123, 0x123, 0x123"
 * @returns FALSE if a critical error with the i8_connection has occurred. Otherwise TRUE.
 */
BOOL send_whitelist(int i8_connection, char *data)
{
	char *p = data;
	ipc_nodelist_t *whitelist = (ipc_nodelist_t *)output_buffer;

	whitelist->header.id = IPC_NODELIST_ID;
	whitelist->list_len = 0;
		
	while(p != NULL && *p != 0)
	{
		uint64_t value = strtoll(p, &p, 0);
		if(value != 0)
		{
			whitelist->list[whitelist->list_len++] = value;
			DBG("add to whitelist: 0x%llx", (long long)whitelist->list[whitelist->list_len - 1]);
		} else {
			ERR("Invalid id received. Ignoring this list.");
			return TRUE;
		}

		while(*p == ' ' || *p == ',')
			p++;
	}

	whitelist->header.payload_size = sizeof(*whitelist) - sizeof(ipc_header_t) + (whitelist->list_len - 1) * sizeof(whitelist->list[0]);
	
	DBG("whitelist->header.payload_size = %d", whitelist->header.payload_size);
	
	LOG("Sending whitelist (%d entries)...", whitelist->list_len);
	if(send(i8_connection, whitelist, sizeof(ipc_header_t) + whitelist->header.payload_size, MSG_NOSIGNAL) == -1)
	{
		ERR("Failed to send whitelist. Send returned: %s (%d)", strerror(errno), errno);
		return FALSE;
	}
	
	return TRUE;
} 


/*
 * @returns FALSE if there is something wrong with any connection.
 */

BOOL receive_from_server(int i8_connection, stomp_connection *subscribe_connection, char *write_queue, char *namespace, char *gateway_id, apr_pool_t *parent_pool)
{
	BOOL retval;
	apr_pool_t *pool = NULL;
	apr_status_t rc;
	
	rc = apr_pool_create(&pool, parent_pool);
	if(rc != APR_SUCCESS)
		APR_ERROR_EXIT("apr_pool_create failed", rc);
	
	BOOL agkflhakflhakljsfderhkgl(int i8_connection, stomp_connection *subscribe_connection, char *write_queue, char *namespace, char *gateway_id, apr_pool_t *pool);
	retval = agkflhakflhakljsfderhkgl(i8_connection, subscribe_connection, write_queue, namespace, gateway_id, pool);
	
	apr_pool_destroy(pool);
	return retval;
}

// This function leaks memory.. use the wrapper above.
BOOL agkflhakflhakljsfderhkgl(int i8_connection, stomp_connection *subscribe_connection, char *write_queue, char *namespace, char *gateway_id, apr_pool_t *pool)
{
	apr_status_t rc;
	stomp_frame *frame;
	int i, num_uid, num_data;
	struct
	{
		char *uid;
		char *data;
	} data[100];

	ipc_message_t *message = (ipc_message_t *)output_buffer;

	
	rc = stomp_read(subscribe_connection, &frame, pool);
	if(rc != APR_SUCCESS)
	{
		APR_ERROR("subscribe_connection", rc);
		return FALSE;
	}

	

	DBG("listener received: %s, %s", frame->command, frame->body);

	gs_data_init();
	num_uid = get_json_value_by_field("uid", data, 0, 2, ARRAY_LENGTH(data), frame->body);
	num_data = get_json_value_by_field("data", data, 1, 2, ARRAY_LENGTH(data), frame->body);

	if(num_uid == 0)
	{
		ERR("Message contains no uid");
		return TRUE;
	}
	
	// Check if the gateway is the receiver.
	if(strcmp(data[0].uid, gateway_id) == 0)
	{
		char *cmd;

		if(num_uid != 1)
		{
			ERR("An array of messages were sent to the gateway. It can only handle one message at the time.");
			return TRUE;
		}

		if(get_json_value_by_field("cmd", &cmd, 0, 1, 1, frame->body) != 1)
		{
			ERR("Failed to get cmd argument from the message sent to the gateway.");
			return TRUE;
		}

		
		if(strcmp(cmd, "clear_whitelist") == 0)
			return send_whitelist(i8_connection, NULL);
		
		if(strcmp(cmd, "add_to_whitelist") == 0)
		{
			if(num_data != 1)
			{
				ERR("Wrong number of elements in the data array in the stomp message. num_data should be 1 and is %d", num_data);
				return TRUE;
			}

			return send_whitelist(i8_connection, data[0].data);
		}
	}


	// Check if we get a different number of uid fields than data fields.
	if(num_data != num_uid)
	{
		ERR("data corruption in stomp message. (num_uid=%d, num_data=%d, command = -->%s<--, body = -->%s<--)", num_uid, num_data, frame->command, frame->body);
		return TRUE;
	}

	num_uid = MIN(num_uid, ARRAY_LENGTH(data));
	for(i = 0; i < num_uid; i++)
	{
		int len;
		
		bzero(output_buffer, sizeof(output_buffer));
		message->header.id = IPC_MESSAGE_ID;
		message->time = 0;
		strncpy(message->source, data[i].uid, sizeof(message->source));
		strncpy(message->data, data[i].data, MAX_I8_PACKAGE_SIZE - sizeof(message));
		len = strlen(message->data);
		message->data_len = len;
		message->header.payload_size = sizeof(*message)- sizeof(message->header) + len;
		 
		printf("uid:  %s\n", data[i].uid);
		printf("data: %s\n", data[i].data);

		LOG("Forwarding message to i8 tranceiver...\n");
		if(send(i8_connection, message, sizeof(ipc_message_t) + len, 0) == -1)
		{
			ERR("Failed to send message to i8 tranceiver. Send returned: %s (%d)", strerror(errno), errno);
			return FALSE;
		}
	}
	
	return TRUE;
}


static void start_server(char *server_string, unsigned int port, char *write_queue, char *namespace, char *gateway_id, apr_pool_t *pool)
{
	struct sockaddr_un local;
	static char subscribe_queue[128];
	int listen_socket, len;
	
	snprintf(subscribe_queue, sizeof(subscribe_queue), SUBSCRIBE_QUEUE_PREFIX "%s.%s", namespace, gateway_id);

	// Create a UNIX socket for the i8 tranceiver.
	if ((listen_socket = socket(AF_UNIX, SOCK_STREAM, 0)) == -1)
	{
		perror("socket");
		exit(1);
	}

	// Bind it.
	local.sun_family = AF_UNIX;
	strcpy(local.sun_path, IPC_SOCKET_PATH);
	unlink(local.sun_path);
	len = strlen(local.sun_path) + sizeof(local.sun_family) + 1;
	if (bind(listen_socket, (struct sockaddr *)&local, len) == -1)
	{
		perror("bind");
		exit(1);
	}

	// Start listen.
	if (listen(listen_socket, 5) == -1)
	{
		perror("listen");
		exit(1);
	}

	// Register signal handler for CTRL-C
	signal(SIGINT, signal_handler);

	while(!gs_die)
	{
		apr_status_t rc;
		stomp_frame frame;
		stomp_connection *write_connection = NULL;
		stomp_connection *subscribe_connection = NULL;

		socklen_t t;
		struct sockaddr_un remote;
		int i8_connection;
		fd_set read_set;

		// Accept the connection.
		LOG("Waiting for a i8 tranceiver connection...");

		// uninstall signal handler temporarily
		signal(SIGINT, NULL);

		t = sizeof(remote);
		if ((i8_connection = accept(listen_socket, (struct sockaddr *)&remote, &t)) == -1)
		{
			perror("accept");
			exit(1);
		}
		
		// Re-install the signal handler
		signal(SIGINT, signal_handler);
		
		LOG("Connected to i8 tranceiver.");

		// Connect to the byteport portal when the i8-tranceiver is connected.
		bm_connect(&write_connection, pool, server_string, port);
		bm_connect(&subscribe_connection, pool, server_string, port);

		// Subscribe to the read queue.
		LOG("Listening to %s", subscribe_queue);
		bzero(&frame, sizeof(frame));
		frame.command = "SUBSCRIBE";
		frame.headers = apr_hash_make(pool);
		apr_hash_set(frame.headers, "destination", APR_HASH_KEY_STRING, subscribe_queue);
		rc = stomp_write(subscribe_connection, &frame, pool);
		if(rc != APR_SUCCESS)
		{
			APR_ERROR("listener: stomp_write failed", rc);
		} else {
			// Prepare a read set for the select function
			FD_ZERO(&read_set);
			FD_SET(i8_connection, &read_set);
			FD_SET(subscribe_connection->socket->socketdes, &read_set);

			while(!gs_die)
			{
				int n;
				fd_set set;

				LOG("Waiting for select");
				set = read_set;
				n = select(FD_SETSIZE, &set, NULL, NULL, NULL);
				
				// Restart the loop if select failed.
				if(n == -1)
				{
					ERR("select failed: %s (%d)", strerror(errno), errno);
					continue;
				}
				
				// Restart the loop if select timed out. (should never happen)
				if(n == 0)
				{
					ERR("select timeout");
					continue;
				}
				
				// Check if the server has something to say.
				if(FD_ISSET(subscribe_connection->socket->socketdes, &set))
					if(receive_from_server(i8_connection, subscribe_connection, write_queue, namespace, gateway_id, pool) == FALSE)
						break;

				// Check if the i8 tranceiver has something to say.
				if(FD_ISSET(i8_connection, &set))
					if(receive_from_i8(i8_connection, write_connection, write_queue, namespace, gateway_id, pool) == FALSE)
						break;
			}
		}
		
		LOG("Disconnected...");
		close(i8_connection);
		bm_disconnect(&subscribe_connection);
		bm_disconnect(&write_connection);
	}
}

static void send_message(char *server_string, unsigned int port, char *write_queue, char *namespace, char *gateway_id, char *message, apr_pool_t *pool)
{
	apr_status_t rc;
	stomp_frame frame;
	stomp_connection *connection = NULL;

	bm_connect(&connection, pool, server_string, port);

	bzero(&frame, sizeof(frame));
	frame.command = "SEND";
	frame.headers = apr_hash_make(pool);
	apr_hash_set(frame.headers, "destination", APR_HASH_KEY_STRING, write_queue);
	frame.body = message;
	frame.body_length = strlen(frame.body);
	rc = stomp_write(connection, &frame, pool);
	if(rc != APR_SUCCESS)
		APR_ERROR_EXIT("sender: stomp_write failed", rc);

	bm_disconnect(&connection);
}


static void start_bombing(char *server_string, unsigned int port, char *write_queue, char *namespace, char *gateway_id, int nr_bombers, int nr_bomb_runs, apr_pool_t *pool)
{
	apr_status_t rc;
	stomp_frame frame;
	stomp_connection *connection = NULL;
	int i;

	for(i = 0; i < nr_bombers; i++)
	{
		if(fork() == 0)
		{
			int x;
			bm_connect(&connection, pool, server_string, port);
			for(x = 0; x < nr_bomb_runs; x++)
			{
				int j;
				char message[1000];
				char data[900];
#if 0				
				for(j = 0; j < sizeof(data); j++)
					data[j] = (rand() % 26) + 'A';
				data[sizeof(data)-1] = 0;
#else
				bzero(data, sizeof(data));
				for(j = 0; j < sizeof(data)/15; j++)
					sprintf(data+strlen(data), "0x%08x,%s", rand(), (rand()%100 > 99)?",":"");
#endif
				//const char *data = gs_str;

				sprintf(message, "{ \"uid\":\"robban-gw-0\", \"cmd\":\"add_to_whitelist\", \"data\":\"%s\"}", data);
			
				bzero(&frame, sizeof(frame));
				frame.command = "SEND";
				frame.headers = apr_hash_make(pool);
				apr_hash_set(frame.headers, "destination", APR_HASH_KEY_STRING, write_queue);
				frame.body = message;
				frame.body_length = strlen(frame.body);
				LOG("frame.body_length = %d", frame.body_length);
				rc = stomp_write(connection, &frame, pool);
				if(rc != APR_SUCCESS)
					APR_ERROR_EXIT("sender: stomp_write failed", rc);
			}
			bm_disconnect(&connection);
			exit(0);
		}
	}
}

int main(int argc, char *argv[])
{
	int opt;
	char *write_queue = NULL;
	char *namespace = NULL;
	char *server_string = NULL;
	char *message = NULL;
	char *gateway_id = NULL;
	unsigned int port = 0;	
	int mode = MODE_UNKNOWN;
	int nr_bombers = 0, nr_bomb_runs = 1000;
	BOOL fail = FALSE;

	apr_status_t rc;
	apr_pool_t *pool = NULL;

	// Parse arguments
	while ((opt = getopt(argc, argv, "n:q:s:p:m:dl:g:b:r:")) != -1)
	{
		switch (opt)
		{
			case 'b':
				nr_bombers = atoi(optarg);
				mode = MODE_BOMBER;
				break;
				
			case 'r':
				nr_bomb_runs = atoi(optarg);
				break;
				
			case 'g':
				gateway_id = optarg;
				break;
				
			case 'n':
				namespace = optarg;
				break;
				
			case 'q':
				write_queue = optarg;
				break;

			case 's':
				server_string = optarg;
				break;

			case 'p':
				port = atoi(optarg);
				break;

			case 'm':
				message = optarg;
				mode = MODE_SEND_MESSAGE;
				break;

			case 'd':
				mode = MODE_DAEMON;
				break;

			case 'l':
				if(strcmp(optarg, "warning") == 0)
					logger_set_level(LOG_WARNING);
				else if(strcmp(optarg, "error") == 0)
					logger_set_level(LOG_ERROR);
				else if(strcmp(optarg, "info") == 0)
					logger_set_level(LOG_INFO);
				else if(strcmp(optarg, "debug") == 0)
					logger_set_level(LOG_DEBUG);
				else
				{
					fail = TRUE;
				}

				break;
		}
	}


	if(gateway_id == NULL || namespace == NULL || write_queue == NULL || server_string == NULL || port == 0 || mode == MODE_UNKNOWN || fail)
	{
		printf("Usage: byteport-stomp-client -s <server> -p <port> -q <queue> -n <namespace> -g <gateway id> [-d | -m <message>] [-l <error | warning | info | debug>]\n");
		return -1;
	}

	// Initialize Apache runtime
	rc = apr_initialize();
	if(rc != APR_SUCCESS)
		APR_ERROR_EXIT("apr_initialize failed", rc);

	// Create apr pool
	rc = apr_pool_create(&pool, NULL);
	if(rc != APR_SUCCESS)
		APR_ERROR_EXIT("apr_pool_create failed", rc);

	if(mode == MODE_DAEMON)
		start_server(server_string, port, write_queue, namespace, gateway_id, pool);

	if(mode == MODE_SEND_MESSAGE)
		send_message(server_string, port, write_queue, namespace, gateway_id, message, pool);

	if(mode == MODE_BOMBER)
		start_bombing(server_string, port, write_queue, namespace, gateway_id, nr_bombers, nr_bomb_runs, pool);

	// APR shutdown
	apr_terminate();
	
	printf("Good bye!\n");

	return 0;
}
