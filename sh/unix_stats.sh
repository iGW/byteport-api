#!/bin/sh

CLIENT_BINARY="curl -s"
DEVICE_UID=`hostname| tr . _`
RATE=60

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [namespace] [namespace api write key]"
    echo ""
    echo "This script will collect a number of common paramters useful for continous logging of a UNIX system"
    echo ""
    echo "The script employs curl or optionally wget to send data to $BYTEPORT_API_HOST using $DEVICE_UID as device UID"
    echo
    exit 1
fi

NAMESPACE=$1
API_KEY=$2
BYTEPORT_BASE_URL="http://api.byteport.se/services/store/$NAMESPACE/$DEVICE_UID/?_key=$API_KEY"
echo "$BYTEPORT_BASE_URL"

# Test base first
response_code=`curl -s -o /dev/null -w "%{http_code}" $BYTEPORT_BASE_URL`

if [ "$response_code" == "403" ]; then
    echo ""
    echo "Error: Byteport responded with "HTTP 403: Forbidden", verify that"
    echo "- The namepspace $NAMESPACE does allow write by HTTP GET and that you supplied the right API key to this script"
    echo "    go to http://www.byteport.se/manager/namespace/security/$NAMESPACE/ to configure this."
    echo ""
    exit $response_code
fi

if [ "$response_code" == "404" ]; then
    echo ""
    echo "Error: Byteport responded with "HTTP 404: Not found", verify that"
    echo "- $NAMESPACE is valid namespace"
    echo "- $DEVICE_UID is a registered device under namespace $NAMESPACE"
    echo "   To register, go to http://www.byteport.se/manager/devices/register/$NAMESPACE/?uid=$DEVICE_UID"
    echo ""
    exit $response_code
fi

while :
do
	mem_free=`free | awk '/Mem:/ { print $4 }'`
		
	data_string="mem_free=$mem_free"

	cmd="curl -I $BYTEPORT_BASE_URL"
	
	echo $cmd

	sleep 60
done
