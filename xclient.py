import asyncio
import ssl
import json


xserver_ip = None
xserver_port = None
client_port  = None
forward_address  = None


conn_list = {}

class XClientServerProtocol:
    async def read_from_server(self,reader,addr):
        while True:
            data = await reader.read(1500) # MTU
            if not data :
                break
            self.transport.sendto(data, addr)

    async def send_to_server(self,message,addr):
        if addr not in conn_list :
            print("Creating new TLS connection for {}".format(addr))
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.VerifyMode.CERT_NONE
            reader, writer = await asyncio.open_connection(xserver_ip, xserver_port,ssl= ssl_ctx)
            conn_list[addr] = (reader,writer)
            writer.write(forward_address.encode())
            await writer.drain()
            await reader.read(1024) 
            loop = asyncio.get_event_loop()
            loop.create_task(self.read_from_server(reader,addr))
        reader, writer = conn_list[addr]
        writer.write(message)
        await writer.drain()
        

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        loop = asyncio.get_event_loop()
        loop.create_task(self.send_to_server(data,addr))
    


async def main():
    with open("./xclient_conf.json") as json_file: 
        obj = json.load(json_file)
        global xserver_port 
        xserver_port = obj["xserver_port"]
        global xserver_ip
        xserver_ip = obj["xserver_ip"]
        global client_port 
        client_port = obj["client_port"]
        global forward_address 
        forward_address = obj["forward_address"]
        

    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: XClientServerProtocol(),
        local_addr=('127.0.0.1', client_port)
    )
    print(f"Listening on 127.0.0.1:{client_port}")
    while True:
        await asyncio.sleep(3600)





if __name__ == '__main__':
    asyncio.run(main())
