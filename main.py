import socket

IP_HOST = "127.0.0.1"
PORTA = 8880

SUCESSO = "200 OK"
ERRO_NOT_FOUND = "404 Not Found"


class Server:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

        self.urls = ["/index.html", "/index.html?usuario="]

    def listen(self, num_solicitation):
        self.sock.listen(num_solicitation)

    def close(self, sock_client):
        sock_client.close()
        print("\n=- Encerrando conexão com cliente -=\n")

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
            print(f"=- IP - {endereco[0]} com porta - {endereco[1]} foi conectado -=")

            self.send_response(client)

            self.close(client)

    # =------ Metodos para trabalhar com os requests do protocolo HTTP ------= #
    def receive_request(self, cliente):
        delimitador = b"\r\n\r\n".decode("utf-8")
        partes = []
        buffer = 1024
        frag = ""
        header = ""

        while True:
            frag = cliente.recv(buffer)
            partes.append(frag)

            msg = b"".join(partes).decode("utf-8")
            if delimitador in msg:
                header = msg[:msg.find(delimitador)]
                break

        return header

    def get_info_request(self, client):
        header = self.receive_request(client)

        linhas = header.splitlines()
        campos = linhas[0].split()

        metodo = campos[0]
        caminho = campos[1]
        versao = campos[2]
        
        return metodo, caminho, versao

    
    # =------ Metodos para trabalhar com os responses do protocolo HTTP ------= #
    def send_response(self, client):
        metodo, caminho, versao = self.get_info_request(client)
        body, status = self.create_body(caminho)
        status_line = f"{versao} {status}"
        header = self.create_header(body)
        campos = []

        status_header = status_line + "\r\n" + header
        campos.append(status_header)
        campos.append(body)


        response = "\r\n\r\n".join(campos)
        response = response.encode("utf-8")
        client.sendall(response)

    def create_header(self, body):
        content_type = "text/html"
        charset = "utf-8"
        content_length = self.get_content_length(body)
        connection = "close"
        campos = []

        Type = f"Content-Type: {content_type}; charset={charset}"
        Length = f"Content-Length: {content_length}"
        conencted = f"Connection: {connection}"

        campos.append(Type)
        campos.append(Length)
        campos.append(conencted)

        header = "\r\n".join(campos)
        return header

    def create_body(self, caminho):
        body = ""
        status = ""

        match caminho:
            case self.urls[0]:
                body = "<h1>Meu servidor HTTP está funcionando!</h1>"
                status = SUCESSO

        if caminho not in self.urls:
            body = "<h1>Erro - caminho não encontrado</h1>"
            status = ERRO_NOT_FOUND

        return body, status

    def get_content_length(self, body):
        msg = body.encode("utf-8")
        return len(msg)



if __name__ == "__main__":
    server = Server()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n=- Servidor interrompido pelo usuário -=")
    finally:
        server.sock.close()