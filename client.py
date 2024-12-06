import asyncio
import sys
import json

async def read_messages(reader):
    while True:
        result_bytes = await reader.readline()
        response = result_bytes.decode()
        if response.strip() == "":
            break
        print(response.strip()) 

async def write_messages(writer):
    while True:
        message = await asyncio.to_thread(sys.stdin.readline)
        writer.write(message.encode())
        await writer.drain()
        if message == "!q":
            break

async def auth(writer, reader):
    write_task = asyncio.create_task(write_messages(writer))
    while True:
        result_bytes = await reader.readline()
        response = result_bytes.decode()
        if response.strip() == '200':
            write_task.cancel()
            return True
        elif response.strip() == '401':
            write_task.cancel()
            return False
        print(response.strip())

def checksum_generator(data: bytes):
    polynomial = 0x1021 
    initial_value = 0xFFFF
    crc = initial_value
    for byte in data:
        crc ^= byte << 8  
        for _ in range(8):  
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial 
            else:
                crc <<= 1  
            crc &= 0xFFFF  
    return crc

async def main():
    global CLIENTPATH
    CLIENTPATH = ".\clientfiles"
    global SERVERPATH
    SERVERPATH = ".\serverfiles"
    server_address, server_port = '127.0.0.1', 8888
    
    print(f'Connecting to file server at {server_address}:{server_port}...')
    reader, writer = await asyncio.open_connection(server_address, server_port)
    authenticated = await auth(writer, reader)
    if authenticated:
        writer.write('Hi\n'.encode())
        message_bytes = await reader.read(1000)
    
        server_msg = message_bytes.decode().strip()
        print(server_msg)        
        req = await asyncio.to_thread(sys.stdin.readline)
        encoded_req = req.encode()
        checksum = checksum_generator(encoded_req)
        
        msg_json = {
            "checksum" :f"{checksum}",
            "encoded_req" : f"{encoded_req}",
            }
        msg_str = json.dumps(msg_json)
        writer.write(msg_str.encode())
        await writer.drain()
        await asyncio.sleep(5)
        writer.close()
        await writer.wait_closed()
        if req.strip() != "!q":
            print("File exchange is done type !q to end the connection")
            while True:
                message = await asyncio.to_thread(sys.stdin.readline) 
                if message.strip() == "!q":
                    break
    else:
        print("Unathorized to access server disconnecting")
    writer.close()
    await writer.wait_closed()
    print("Done")
asyncio.run(main())

