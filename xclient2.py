import asyncio
import ssl


server_ip = 'localhost'
xserver_port = 44443
client_port = 12345
server_port = 4567


conn_list = {}

class EchoServerProtocol:
    async def read_from_server(self,reader,addr):
        while True:
            data = await reader.read(1024)
            if not data :
                break
            response = data.decode()
            print(f'Received response: {response}')
            self.transport.sendto(data, addr)

    async def send_to_server(self,message,addr):
        if addr not in conn_list :
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.VerifyMode.CERT_NONE
            reader, writer = await asyncio.open_connection(server_ip, xserver_port,ssl= ssl_ctx)
            conn_list[addr] = (reader,writer)
            first_adr = f'127.0.0.1:{server_port}'
            writer.write(first_adr.encode())
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
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('127.0.0.1', client_port)
    )
    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()





if __name__ == '__main__':
    asyncio.run(main())