# byteport-api
Collection of open source (BSD Licence) code examples useful for connecting to the IoT cloud service Byteport.

Read all about it here

www.byteport.se and 

Ssign up for an account to get started.

It is **free** for small volume users, such as hobbyists, achademics and startups.

## API documentation
TODO

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
