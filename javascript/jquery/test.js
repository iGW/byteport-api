
var client = ByteportAPIv1();

function test_should_echo_byteport() {
    client.echo(function(data) {
        console.log("ECHO result: "+data);
    })
}