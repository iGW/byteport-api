# byteport-api
Collection of open source (BSD Licence) code examples useful for connecting to the IoT cloud service Byteport.

Read all about it here

www.byteport.se and 

Ssign up for an account to get started.

It is **free** for small volume users, such as hobbyists, achademics and startups.

### Python teaser one - storing numbers
```
from http_clients import ByteportHttpGetClient
import time

client = ByteportHttpGetClient('myownspace', 'f00b4s3cretk3y', 'barDev1')

client.store({'style': 1337})
time.sleep(1)
client.store({'style': 1338})
time.sleep(1)
client.store({'style': 1339})

```

### Python teaser two - storing a file as an object
```
from http_clients import ByteportHttpPostClient

client = ByteportHttpPostClient('myownspace', 'f00b4s3cretk3y', 'barDev1')

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
3. In the box **API settings** change *HTTP Write method* to allow storage using the HTTP GET and/or POST APIs.
4. Use *API Write key* when trying out the client examples below. You can set a new one, or use the generated. Leave blank to generate a new.

## Client implementations
### Python
The reference implementation is made in Python. But the HTTP API can of course be accessed using any language. Python is clear and simple enough to be used as a

#### Install
```
 $ git clone https://github.com/iGW/byteport-api/
 $ cd byteport-api
 $ python ./setup.py install
```

#### Usage
Have a look at the use-cases at the [integration test suite](https://github.com/iGW/byteport-api/blob/master/python/byteport/integration_tests.py).
