from control_lab_lisa import Server

server = Server()
# python -m control_lab_lisa --ip-address 127.0.0.1 --port 50052 --insecure
try:
    server.start("127.0.0.1", 50052)
    # do something
finally:
    server.stop()