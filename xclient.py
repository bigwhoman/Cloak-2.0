#!/usr/bin/env python3

import asyncio
import ssl

def addr_to_string(addr: tuple[str, int]) -> int:
    return addr[0] + ":" + str(addr[1])

class EchoServerProtocol:
    def __init__(self) -> None:
        self._address_map = {}
        self._address_map_lock = asyncio.Lock()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(type(data))
        #print('Received %r from %s' % (message, addr))
        #print('Send %r to %s' % (message, addr))
        self.transport.sendto(data, addr)

    async def handle_datagram(self, data: bytes, addr: tuple[str, int]):
        async with self._address_map_lock:
            if addr_to_string(addr) not in self._address_map:
                # Create a TLS connection to server
                ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.VerifyMode.CERT_NONE
                reader, writer = await asyncio.open_connection('127.0.0.1', 44443, ssl=ssl_ctx)
                # Send handshake
                writer.write(addr_to_string(addr).encode())
                await writer.drain()
                ack_packet = await reader.read(3)
                if ack_packet.decode() != "ack":
                    raise Exception("invalid ack packet")
                # Setup the reader
                asyncio.create_task(self.read_from_tls(reader, addr))
                # Save it to map
                self._address_map[addr_to_string(addr)] = writer

        # Now we are sure that a TLS connection exists in the hashmap
        writer: asyncio.StreamWriter = self._address_map[addr_to_string(addr)]
        writer.write(data)
        await writer.drain()

    async def read_from_tls(self, tls_reader: asyncio.StreamReader, addr: tuple[str, int]):
        try:
            while True:
                data = await tls_reader.read(1500) # MTU
                if not data:
                    break
                self.transport.sendto(data, addr) # Send to socket
        except:
            pass
        # Close the tls
        async with self._address_map_lock:
            if addr_to_string(addr) not in self._address_map:
                self._address_map[addr_to_string(addr)].close()
                await self._address_map[addr_to_string(addr)].wait_closed()
                del self._address_map[addr_to_string(addr)]
                

async def setup_server():
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('127.0.0.1', 9999))
    print("Started the UDP server")
    # Never exit the app
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(setup_server())