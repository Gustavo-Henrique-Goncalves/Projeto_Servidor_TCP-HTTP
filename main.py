import socket

IP_HOST = "127.0.0.1"
PORTA = 8880


class Server:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def listen(self, num_solicitation):
        self.sock.listen(num_solicitation)

    def close(self, sock_client):
        sock_client.close()

    def accept_solicitation(self):
        client, endereco = self.sock.accept()
        return client, endereco

    def start_server(self):
        self.sock.bind((IP_HOST, PORTA))
        self.listen(1)
        self.main_loop()

    def main_loop(self):
        print("=- Servidor está escutando...")

        while True:
            client, endereco = self.accept_solicitation()
            print(
                f"=- IP - {endereco[0]} com porta - {endereco[1]} foi conectado -="
            )

            # A comunicação com o cliente será implementada aqui.
            self.close(client)


if __name__ == "__main__":
    server = Server()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n=- Servidor interrompido pelo usuário -=")
    finally:
        server.sock.close()