# byteport-api
Collection of open source (BSD Licence) code examples useful for connecting to the IoT cloud service Byteport.

Read all about it here

www.byteport.se and 

Sign up for an account to get started.

It is **free** for small volume users, such as hobbyists, academics and start-ups.


### Python example 1 - storing numbers
A common use-case is to send some data at regular intervals
```
from http_clients import ByteportHttpGetClient
import time

# Will send a single empty heart beat packet.
client = ByteportHttpClient('myownspace', 'f00b4s3cretk3y', 'barDev1')

while True:
    # Store a string and the current UNIX Epoch time on a regular interval
    client.store({'info': 'All systems nominal', 'current_time': time.time()})
    time.sleep(60)

```

### Python example 2 - storing file content as value
A file is read and the content of the file is stored as value to the field called temperature.
```
from http_clients import ByteportHttpGetClient
import time

# Will send a single empty heart beat packet.
client = ByteportHttpClient('myownspace', 'f00b4s3cretk3y', 'barDev1')

# Will raise exception upon errors
client.store_file('temperature', './current_temperature')
```

### Python example 3 - storing file content as value after encoding
In this case a single file is read, compressed, encoded and sent to byteport with a few lines of code.
```
from http_clients import ByteportHttpPostClient

client = ByteportHttpClient('myownspace', 'f00b4s3cretk3y', 'barDev1')

path_to_interesting_file = '/tmp/status_data'

client.base64_encode_and_store_store_file('staus_files', path_to_interesting_file, compression='bzip2')

```

## API documentation
### Byteport data model
Byteport accepts:
* Numbers
* Text
* Objects

And so you may specify what kind of object you are storing by assigning a media type (formerly termed MIME-type) that will be supplied when fetching the data again.

### Considerations to HTTP GET API
While storing data usign HTTP GET calls might seem a bit backwards. But it is sometimes a nice feature for quick and dirty scenarios. The only caveat is the data size **limitation of 2 Kb**.

### Storing objects
To store data blocks **larger than 2K** you must use other methods available. For HTTP you can use the POST call instead. The reference implementations below all contain methods for storing objects. Binary data needs to be base64 encoded before storing. And before doing that, you might as well apply some compression to save some bandwidth and Byteport storage space.


## General preparations
Independent of client technology, do the following steps to ensure you can store data using the HTTP API

1. Create a new namespace in Byteport: http://www.byteport.se/manager/namespaces/
2. Open up the namespace and click the **Security** tab.
3. In the box **API settings** change *HTTP Write method* to allow storage using the HTTP GET and POST methods.
4. Use *API Write key* when trying out the client examples below. You can set a new one, or use the generated. Leave blank to generate a new.

## Client implementations
### Python
The reference implementation is made in Python. But the HTTP API can of course be accessed using any language. Python is clear and simple enough to be used as a

#### Install
Pytz is so good it should be in the standard library. It is not yet, so we have to pip it.
```
 $ git clone https://github.com/iGW/byteport-api/
 $ cd byteport-api/python
 $ pip install -r requirements.txt
 $ python ./setup.py install
```

#### Usage
Have a look at the use-cases at the [integration test suite](https://github.com/iGW/byteport-api/blob/master/python/byteport/integration_tests.py).
