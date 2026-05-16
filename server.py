import socket
import threading
import os
import select
import sys

recievingf = threading.Event()
recievingf.set()
close = threading.Event()

def fileRCV(connect, name, size):
    file = open(f'recieved files/{name}', 'wb')
    rcvd = 0
    while rcvd<size:
        message = connect.recv(min(1024, size-rcvd))
        file.write(message)
        rcvd+=len(message)
    file.write("this file is stored by the server".encode())
    file.close()
    print(open(f'recieved files/{name}', 'r').read())

def fileSend(connection, name):
    size = os.path.getsize(f'recieved files/{name}')
    connection.send(f'{f"file|{name}|{size}":<1024}'.encode())
    print(f"sending file: {name}")
    file = open(f'recieved files/{name}', 'rb')
    sent = 0
    while sent < size:
        send = file.read(min(1024,size-sent))
        connection.send(send)
        sent+=len(send)
    file.close()
    print(f"{name} sent")

def listen(connection):
    while True:
        if select.select([connection],[],[])[0]:
            mtype, message, *size = connection.recv(1024).decode().split('|')
            if (size):
                size=int(size[0])
            if (mtype == 'msg'):
                print(message)
                if (message == "Bye from client"):
                    connection.send(f"msg|Bye from server".encode())
                    close.set()
                    break
            elif (mtype == 'file'):
                fileRCV(connection, message, size)
                fileSend(connection, message)

def sender(connection):
    while True:
        recievingf.wait()
        message = input()
        connection.send(f"msg|{message}".encode())

if (os.path.isfile("settings.txt")):
    try:
        with open("settings.txt") as f:
            lines = f.read().split("\n")
            HOST = lines[0].split(":")[-1]
            PORT = int(lines[1].split(":")[-1])
    except:
        print("Your settings.txt may be formated incorrectly please ensure it follows this format: \n HOST:x.x.x.x \n PORT:xxx")
else:
    print("could not find settings.txt, please ensure you have a settings.txt in the running directory with the following format: \n HOST:x.x.x.x \n PORT:xxx")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server.bind((HOST,PORT))

    server.listen()
    connection, address = server.accept()
    print(f"Connected by {address}")
    print(f"{connection.recv(1024).decode()}")
    connection.send(f"msg|Hello from Server {socket.gethostname()}".encode('utf-8'))
    sending = threading.Thread(target=sender, args={connection,}, daemon=True)
    recieving = threading.Thread(target=listen, args={connection,})
    sending.start()
    recieving.start()

    recieving.join()
finally:
    connection.close()