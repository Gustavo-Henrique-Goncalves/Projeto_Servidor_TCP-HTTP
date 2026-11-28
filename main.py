import socket
from urllib.parse import urlparse, parse_qs
import threading 


# =- Definindo Constantes importantes -=
# =- endereço do host 
IP_HOST = "127.0.0.1"
PORTA = 8880

# =- limite de requisições que o servidor pode receber, até bloquear
REQUEST_LIMITS = 5

# =- casos de erro possiveis
SUCESSO = "200 OK"
ERROR_NOT_FOUND = "404 Not Found"
ERROR_METHOD_NOT_ALLOWED = "405 Method Not Allowed"
ERROR_SERVICE_UNAVAILABLE = "503 Service Unavailable"

# =- definição da classe do servidor
class Server:
    # =------ Metodos relacionados ao Socket ------= #
    # Construtor
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

        # variaveis do servidor
        self.urls = ["/index.html", "/reiniciar"]   # caminhos disponiveis
        self.count_requisition = 0                  # contador de requisições
        self.running = True                         # define se o servidor está ativo ou não

    # define quantos clientes o servidor irá se conectar por vez
    def listen(self, num_solicitation):
        self.sock.listen(num_solicitation)

    # encerra a conexão do cliente
    def close(self, sock_client):
        sock_client.close()
        print("=- [ENCERRAMENTO] - Encerrando conexão com cliente -=\n")

    # aceita a solicitação de conexão
    def accept_solicitation(self):
        client, endereco = self.sock.accept()
        return client, endereco

    # configurando a inicialização do servidor
    def start_server(self):
        self.sock.bind((IP_HOST, PORTA))
        self.listen(1)

        self.sock.settimeout(5)

        # criação das threads para cada funcionalidade do servidor
        thread_servidor = threading.Thread(target=self.main_loop)       # thread que irá manter o servidor ativo
        thread_comand_read = threading.Thread(target=self.read_command) # thread que irá analisar apenas se algum comando foi digitado

        thread_servidor.start()
        thread_comand_read.start()

        thread_servidor.join()
        thread_comand_read.join()


     # =------ Loop Principal do servidor ------= # =------------------------------------------=
    
    def main_loop(self):
        print("=- Servidor está escutando...")

        # enquanto servidor estiver ativo
        while self.running:
            # se algum cliente enviou uma solicitação, aceite
            try:
                client, endereco = self.accept_solicitation()
                print(f"=- [CONEXÃO] - IP :{endereco[0]} com porta - {endereco[1]} -=")
            except socket.timeout:
                print("=- [ERRO] - tempo de espera de uam nova conexão excedido -=")
                continue

            client.settimeout(5)

            try:
                self.send_response(client)
            except ValueError as e:
                print(e)
            except socket.timeout:
                print("=- [ERRO] - Tempo do cliente esgotou -=")
                continue
            finally:
                self.close(client)

        print("\n=- [ENCERRAMENTO] - Encerrando Servidor -=\n") 
        return

    # =------ Metodos para trabalhar com os requests do protocolo HTTP ------= # =------------------------------------------=
    # =- recebe a requisição
    def receive_request(self, cliente):
        delimitador = b"\r\n\r\n".decode("utf-8")
        partes = []
        buffer = 1024
        frag = ""
        header = ""

        # enquanto estiver recebendo as mensagens
        while True:
            # recebe o fragmento de mensagem do tamanho do buffer configurado
            frag = cliente.recv(buffer)

            # verifica se o fragmento vier vazio, sem sinal de delimitador, logo descobrindo que a conexão foi encerrada antes do recebimento total da requisição
            if frag == b"":
                raise ValueError("\n=- [ERRO] - Conexão encerrada durante recebimento de requisição -=\n")

            partes.append(frag)

            # junta as mensagens e analisa se o delimitador de final do cabeçalho entá dentre as mensagens
            msg = b"".join(partes).decode("utf-8")
            if delimitador in msg:
                header = msg[:msg.find(delimitador)]
                break

        return header

    # =- Recebe os dados baseados na requisição
    def get_info_request(self, client):
        header = self.receive_request(client)

        linhas = header.splitlines()
        campos = linhas[0].split()

        # dados informados na requisição
        metodo = campos[0] 
        caminho = campos[1]
        versao = campos[2]

        print(f"=- [REQUISIÇÃO] - {metodo} {caminho} {versao} -=")
        
        return metodo, caminho, versao

    
    # =------ Metodos para trabalhar com os responses do protocolo HTTP ------= # =------------------------------------------=
    # =- Manda uma resposta para o cliente
    def send_response(self, client):
        # para isso o servidor tem que criar uma mensagem HTTP para responder o cliente
        # =- Para isso o servidor precisa saber

        # Do metodo, caminho e versão recebidas pela requisição
        metodo, caminho, versao = self.get_info_request(client)

        # a partir disso o servidor analisa o caminho e retorna o corpo da resposta de acordo, alem do status da analise
        body, status = self.analise_path(caminho, metodo)
        print(f"=- [RESPOSTA] - status : {status} -=")

        # apenas utiliza a versao do protocolo para poder utilizar na status_line
        status_line = f"{versao} {status}"

        # cria cabeçalho, utilizando o body apenas para ver quantos bytes o corpo da resposta possui
        header = self.create_header(body, status)
        campos = []

        # juntando as informações criadas e colocando um delimitador separando o cabeçalho do corpo
        status_header = status_line + "\r\n" + header
        campos.append(status_header)
        campos.append(body)


        response = "\r\n\r\n".join(campos)

        # converte o texto para bytes e manda para o cliente
        response = response.encode("utf-8")
        client.sendall(response)

    # =- Criação do cabeçalho
    def create_header(self, body, status):
        content_type = "text/html"
        charset = "utf-8"
        content_length = self.get_content_length(body) # analisa o corpo e define o tamanho dele dinamicamente
        connection = "close"
        campos = []

        Type = f"Content-Type: {content_type}; charset={charset}"
        Length = f"Content-Length: {content_length}"
        conencted = f"Connection: {connection}"

        campos.append(Type)
        campos.append(Length)
        campos.append(conencted)

        # variavels status para ver se, baseado no erro recebido, precisa de mais campos no cabeçalho ou não 
        if status == ERROR_METHOD_NOT_ALLOWED:
            Allow = "Allow: GET"
            campos.append(Allow)

        header = "\r\n".join(campos)
        return header

    # Cria corpo da resposta baseado na analise do caminho
    def create_body(self, caminho, parametros, metodo_permitido):
        body = ""
        status = ""

        # =- verifica se o caminho existe na lista de caminhos
        # =- Criterio de status:
        # 1 - 200 OK - Sucesso na conexão
        # 2 - 404 - se o caminho for desconhecido
        # 3 - 405 - se o metodo recebido não é permitido (no caso só é permitido receber requisições do metodo GET)
        # 4 - 503 - se o numero de requisições passou do limite 
        match caminho:
            case "/index.html":
                if metodo_permitido:
                    if self.count_requisition > REQUEST_LIMITS:
                        body = "<h1>Erro - Limite de requisições ultrapassado </h1>"
                        status = ERROR_SERVICE_UNAVAILABLE
                    else:
                        body = "<h1>Meu servidor HTTP está funcionando!</h1>"
                            
                        if parametros is not None:
                            body = f"<h1>Olá {parametros[0]} do IP: {IP_HOST}:{PORTA}!</h1>"
                        status = SUCESSO
                else:
                    body = "<h1>Erro - Método não permitido</h1>"
                    status = ERROR_METHOD_NOT_ALLOWED
            case "/reiniciar":
                if metodo_permitido:
                    body = "<h1>Reiniciando Servidor</h1>"
                    self.reset_count()
                    status = SUCESSO
                else:
                    body = "<h1>Erro - Método não permitido</h1>"
                    status = ERROR_METHOD_NOT_ALLOWED

            case _:
                body = "<h1>Erro - caminho não encontrado</h1>"
                status = ERROR_NOT_FOUND

        return body, status

    # analisa o caminho, procurando parametros adicionais 
    def analise_path(self, caminho, metodo):
        analise = urlparse(caminho)

        caminho_definido = analise.path
        query = parse_qs(analise.query)

        # verifica se o caminho possui o parametro "usuario"
        parametros = query.get("usuario")

        if caminho_definido not in self.urls: 
            return self.create_body(caminho_definido, parametros, None)

        # o contador de requisição só será incrementado se na requisição possuir um metodo valido e um caminho existente na lista de caminhos disponiveis
        metodo_valido = self.validate_method(metodo)
        if metodo_valido and caminho_definido != "/reiniciar":
            self.add_count()
        return self.create_body(caminho_definido, parametros, metodo_valido)

    # apena valida o metodo
    def validate_method(self, method):
        if method == "GET":
            return True
        else:
            return False

    # incrementa o contador 
    def add_count(self):
        self.count_requisition += 1

    # Reseta o contador 
    def reset_count(self):
        self.count_requisition = 0

    # calcula dinamicamente o tamanho do corpo
    def get_content_length(self, body):
        msg = body.encode("utf-8")
        return len(msg)

    # =------ Metodos para trabalhar com o multithreding do servidor ------= # =------------------------------------------=

    # espera o servidor receber algum tipo de comando, se receber a tecla "Q" ou "q", ele encerra o servidor
    def read_command(self):
        while self.running:
            tecla = input("=- Digite o comando: ")

            if tecla.lower() == "q":
                self.running = False
        return




# =----------------------------------------------------------------------------------------------------------------------=

if __name__ == "__main__":
    server = Server()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n=- Servidor interrompido pelo usuário -=")
    finally:
        server.sock.close()