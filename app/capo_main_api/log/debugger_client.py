import socket
import time
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 12123        # The port used by the server

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # While sokcet is connected
            while s.fileno() != -1:
                # if s.recv(1024) == b'':
                #     s.close()
                #     break
                # else:
                #     print('here')
                data = s.recv(1024)
                print(data.decode('ascii'))
                s.close()
            
    except KeyboardInterrupt:
        s.close()
    except ConnectionResetError:
        pass
    except ConnectionRefusedError:
        s.close()
        time.sleep(0.1)
        pass
    
# print('Received', repr(data))