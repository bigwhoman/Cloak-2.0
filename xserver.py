#!/usr/bin/env python3

import asyncudp
import asyncio
import ssl

# From https://gist.github.com/zapstar/a7035795483753f7b71a542559afa83f

def parse_address(address: str) -> tuple[str, int]:
    index = address.rfind(':')
    return (address[:index], int(address[index+1:]))

async def copy_to_udp(tcp_reader: asyncio.StreamReader, udp_writer: asyncudp.Socket):
    while True:
        try:
            data = await tcp_reader.read(1500) # MTU
            if not data: # done!
                break
            udp_writer.sendto(data)
            await asyncio.sleep(0.001)
        except:
            break # fuck up
    udp_writer.close()

async def copy_from_udp(reader: asyncudp.Socket, writer: asyncio.StreamWriter):
    while True:
        try:
            data, _ = await reader.recvfrom()
            if not data: # done!
                break
            writer.write(data)
            await writer.drain()
        except:
            break # fuck up
    writer.close()
    await writer.wait_closed()

async def handle_connection(server_reader: asyncio.StreamReader, server_writer: asyncio.StreamWriter):
    addr = server_writer.get_extra_info('peername')
    print('Connection established with {}'.format(addr))
    # Read the destination address
    destination_address = parse_address((await server_reader.read(20)).decode("utf-8"))
    print('Proxy {} to {}'.format(addr,  destination_address))
    # Create the client
    sock = await asyncudp.create_socket(remote_addr=destination_address)
    # Ack client
    server_writer.write(b'ack')
    await server_writer.drain()
    # Proxy data
    task1 = asyncio.create_task(copy_to_udp(server_reader, sock))
    task2 = asyncio.create_task(copy_from_udp(sock, server_writer))
    await task1
    await task2
    print('Done with {}'.format(addr))


async def setup_server():
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.load_cert_chain('cert.pem', keyfile='key.pem')
    ssl_ctx.check_hostname = False
    server = await asyncio.start_server(handle_connection,
                                     '127.0.0.1',
                                     44443,
                                     ssl=ssl_ctx)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    async with server:
        await server.serve_forever()
    


if __name__ == '__main__':
    asyncio.run(setup_server())