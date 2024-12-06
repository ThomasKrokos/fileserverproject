import asyncio
import shutil
import os
import json

def move_file(source_dir, dest_dir, filename):
    os.makedirs(dest_dir, exist_ok=True)

    source_path = os.path.join(source_dir, filename)
    destination_path = os.path.join(dest_dir, filename)

    try:
        shutil.move(source_path, destination_path)
        print(f"Moved {filename} from {source_dir} to {dest_dir}")
    except FileNotFoundError:
        print(f"File {filename} not found in {source_dir}")
        raise FileNotFoundError
    except Exception as e:
        print(f"Error occurred: {e}")
        raise e


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


async def file_handler(reader, writer):
    while True:
        encoded_request = await reader.read()
        req_str = encoded_request.decode()
        req_json = json.loads(req_str)        
        req = eval(req_json["encoded_req"]).decode()
        if req == "!q":
            return
        server_checksum = checksum_generator(eval(req_json["encoded_req"]))
        print(f"Client generated checksum: {req_json['checksum']}")
        print(f"Sever generated checksum: {server_checksum}")
        if req_json['checksum'] != f'{server_checksum}':
            print("Checksums do not match, cancelling file move")
            return
        else: 
            print("Checksums match, continuing with file move")
        
        print(f"request is {req}")
        request = req.split(' ')
        type = request[0]
        filename = request[1].strip()
        print(f"type = {type}, filename = {filename}, ")

        try:
            if type == "put":
                move_file(CLIENTPATH, SERVERPATH, filename)
                writer.write('200'.encode())
                return

            if type == "get":
                move_file(SERVERPATH, CLIENTPATH, filename)
                writer.write('200'.encode())
                return
            else:
                print("type was wrong")
                return
        except Exception as e:
            print(f"An error occurred in functionb: {e}")

async def handle_client(reader, writer):
    otp = "qwe123"
    print('Client attempting authentication')
    writer.write('Welcome to the File Server\n'.encode())
    await writer.drain()
    writer.write('Please enter password to access server:\n'.encode())
    await writer.drain()
    msg_encoded = await reader.readline()
    msg = msg_encoded.decode().strip()
    print(f'Got: {msg}')
    if msg == otp:
        writer.write('200\n'.encode())
        await writer.drain()
        print('Client authentication succeeded\n')
        msg_encoded = await reader.readline()
        msg = msg_encoded.decode().strip()
        print(f'Message from client: {msg}')
        if msg == 'Hi':
            writer.write('Hello\nPick what you want to do\nput <filename> to upload a file \nget <filename> to download a file\n!q to exit'.encode())
            await writer.drain()
            await file_handler(reader, writer)
    else:
        writer.write('401\n'.encode())
        await writer.drain()
        print('Client authentication failed')
    await asyncio.sleep(1)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print('Connection closed')
 
async def main():
    global CLIENTPATH
    CLIENTPATH = ".\clientfiles"
    global SERVERPATH
    SERVERPATH = ".\serverfiles"
    host_address, host_port = '127.0.0.1', 8888
    server = await asyncio.start_server(handle_client, host_address, host_port)
    async with server:
        print('File server running...')
        await server.serve_forever()
 
asyncio.run(main())