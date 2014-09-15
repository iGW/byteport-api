#!/bin/bash
#  www.byteport.se
#    Simple example client using cURL (curl.haxx.se)
#
########################################################

CURL_BASE="curl -s"
NAMESPACE=$1
API_KEY=$2
RATE=60
BYTEPORT_API_HOST="api.byteport.se"

########################################################
# collecting commands
#

# Check for binaries
hash curl 2>/dev/null || { echo >&2 "This program require cURL but it's not installed. Aborting."; exit 1; }

if [ -n "$3" ]; then
    DEVICE_UID=$3
else
    DEVICE_UID=`hostname| tr . _`
fi

BYTEPORT_BASE_URL="http://$BYTEPORT_API_HOST/services/store/$NAMESPACE/$DEVICE_UID/?_key=$API_KEY"

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 [namespace] [namespace api write key] <device_uid (optional)>"
    echo ""
    echo "This script will collect a number of common paramters useful for continous logging of a UNIX system"
    echo ""
    echo "The script employs curl or optionally wget to send data to $BYTEPORT_API_HOST"
    echo
    exit 1
fi
echo "Namespace  = $NAMESPACE"
echo "Device UID = $DEVICE_UID"
echo "Base URL = $BYTEPORT_BASE_URL"

# Test base first
response_code=`curl -s -o /dev/null -w "%{http_code}" $BYTEPORT_BASE_URL`

if [ "$response_code" == "200" ]; then
    echo "Byteport API test call OK!"
fi

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
    echo "- $NAMESPACE is valid namespace and open for access"
    echo "- $DEVICE_UID is a registered device under namespace $NAMESPACE"
    echo "   To register, go to http://www.byteport.se/manager/devices/register/$NAMESPACE/?uid=$DEVICE_UID"
    echo ""
    exit $response_code
fi

while :
do	
	rdv=`df -k / | awk '$3 ~ /[0-9]+/ { print $4 }'`
	la5v=`uptime | awk '{ print $11 }'| tr -d ','`
	data_string="rd_free=$rdv&la5=$la5v"

	`curl -s "$BYTEPORT_BASE_URL&$data_string"`

	sleep 60
done
