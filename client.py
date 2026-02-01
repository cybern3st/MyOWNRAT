import threading
import logging
import socket
import ssl
import os
from cryptography.fernet import Fernet, InvalidToken

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

# Configurazione percorsi certificati
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_DIR = os.path.join(BASE_DIR, "certs")

# Chiave FERNET condivisa tra client e server
FERNET_KEY = b'2q7UuYx7ep2xJZL-G6fJ0X4Oq9c0xv7Q0i0n2c8pN7o='
fernet = Fernet(FERNET_KEY)


class CLIENT:
    STATUS = "Active"
    MESSAGE = ""
    KEY = "#@JEBUN@#"

    def __init__(self, sock, addr):
        """
        sock : socket SSL già accettata dal server
        addr : tupla (ip, porta) restituita da accept()
        """
        self.sock = sock
        self.ip = addr[0]
        self.port = addr[1]

    def acceptor(self):
        """Thread che riceve e decifra messaggi dal client"""
        buffer = b""  # Usa bytes, non string!

        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    self.STATUS = "Disconnected"
                    logging.info(f"[{self.ip}:{self.port}] Disconnesso")
                    break

                # Accumula i bytes nel buffer
                buffer += chunk

                # Controlla se abbiamo ricevuto la KEY (fine messaggio)
                key_bytes = self.KEY.encode('utf-8')
                if key_bytes in buffer:
                    # Trova la posizione della KEY
                    idx = buffer.find(key_bytes)

                    # Estrai il token Fernet (tutto prima della KEY)
                    token_bytes = buffer[:idx]

                    # Rimuovi il messaggio processato dal buffer
                    buffer = buffer[idx + len(key_bytes):]

                    try:
                        # Decifra il token (che è già in bytes)
                        decrypted = fernet.decrypt(token_bytes)
                        self.MESSAGE = decrypted.decode('utf-8')
                        logging.debug(
                            f"[{self.ip}:{self.port}] Messaggio ricevuto: {self.MESSAGE}"
                        )
                    except InvalidToken:
                        logging.error(
                            f"[{self.ip}:{self.port}] Token Fernet non valido"
                        )
                        self.MESSAGE = ""
                    except UnicodeDecodeError:
                        # Se non è UTF-8, mantieni i bytes
                        self.MESSAGE = decrypted
                        logging.warning(
                            f"[{self.ip}:{self.port}] Messaggio non UTF-8, "
                            f"probabilmente dati binari"
                        )

                    if not self.MESSAGE:
                        self.MESSAGE = " "

            except ssl.SSLError as e:
                logging.error(f"[{self.ip}:{self.port}] Errore SSL: {e}")
                self.STATUS = "Disconnected"
                break
            except Exception as e:
                logging.error(f"[{self.ip}:{self.port}] Errore: {e}")
                self.STATUS = "Disconnected"
                break

    def engage(self):
        """Avvia il thread di ricezione"""
        t = threading.Thread(target=self.acceptor)
        t.daemon = True
        t.start()
        logging.info(f"[{self.ip}:{self.port}] Thread acceptor avviato")

    def send_data(self, val):
        """Cifra e invia una stringa al client"""
        try:
            # Cifra con Fernet
            token = fernet.encrypt(val.encode('utf-8'))
            payload = token + self.KEY.encode('utf-8')
            self.sock.sendall(payload)
            logging.debug(f"[{self.ip}:{self.port}] Inviato: {val}")
        except Exception as e:
            logging.error(f"[{self.ip}:{self.port}] Errore invio: {e}")
            self.STATUS = "Disconnected"

    def recv_data(self, timeout=30):
        """
        Attende e restituisce il prossimo messaggio completo.

        Args:
            timeout: secondi di attesa massimi prima di restituire None

        Returns:
            str: messaggio ricevuto, o None se disconnesso/timeout
        """
        import time
        start_time = time.time()

        while not self.MESSAGE:
            try:
                if self.STATUS == "Disconnected":
                    logging.warning(f"[{self.ip}:{self.port}] recv_data: client disconnesso")
                    return None

                # Controlla timeout
                if timeout and (time.time() - start_time) > timeout:
                    logging.warning(f"[{self.ip}:{self.port}] recv_data: timeout dopo {timeout}s")
                    return None

                time.sleep(0.01)  # Evita busy-wait al 100% CPU

            except KeyboardInterrupt:
                return None

        rtval = self.MESSAGE
        self.MESSAGE = ""
        return rtval

    def close(self):
        """Chiude la connessione"""
        try:
            self.sock.close()
            self.STATUS = "Disconnected"
            logging.info(f"[{self.ip}:{self.port}] Connessione chiusa")
        except Exception as e:
            logging.error(f"[{self.ip}:{self.port}] Errore chiusura: {e}")

    def is_connected(self):
        """Verifica se il client è ancora connesso"""
        return self.STATUS == "Active"


def start_server(host="0.0.0.0", port=4443):
    """
    Avvia il server SSL/TLS che accetta connessioni e crea oggetti CLIENT
    """
    # Configura contesto SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile=os.path.join(CERT_DIR, "server.crt"),
        keyfile=os.path.join(CERT_DIR, "server.key"),
    )

    # Lista per tenere traccia dei client connessi
    clients = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(5)
        logging.info(f"Server in ascolto su {host}:{port} (SSL/TLS)")

        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                try:
                    # Accetta connessione SSL
                    conn, addr = ssock.accept()
                    logging.info(f"Nuova connessione da {addr[0]}:{addr[1]}")

                    # Crea oggetto CLIENT e avvia il thread di ricezione
                    client = CLIENT(conn, addr)
                    client.engage()
                    clients.append(client)

                    # Esempio: invia messaggio di benvenuto
                    client.send_data("Benvenuto sul server!")

                    # Puoi gestire i client in thread separati o con logica custom
                    # threading.Thread(target=handle_client, args=(client,)).start()

                except KeyboardInterrupt:
                    logging.info("Server interrotto da utente")
                    break
                except Exception as e:
                    logging.error(f"Errore accettazione connessione: {e}")

    # Chiudi tutti i client
    for client in clients:
        client.close()


def handle_client(client):
    """
    Esempio di funzione per gestire un client in un thread separato
    """
    while client.STATUS == "Active":
        msg = client.recv_data()
        if msg is None:
            break

        logging.info(f"[{client.ip}:{client.port}] Ricevuto: {msg}")

        # Echo del messaggio
        client.send_data(f"Echo: {msg}")


if __name__ == "__main__":
    # Avvia il server
    start_server()