
from byteport.http_clients import ByteportHttpClient

#
# NOTE: Needs a proxy set up on port 5000, first to this from shell:
#
# (venv-byteport-api) hans@Hanss-MacBook-Pro:~/Development/igw/git_clones/byteport-api$ ssh -i ./id_rsa -D 5000 -N gateway@marder.igw.se &
#

byteport_client = ByteportHttpClient('mloc', 'f5770ca3ac1ff64de7f0bc70', 'locator8',  proxy_port=5000)

byteport_client.store({'eth0_rx_mb': '10'})
