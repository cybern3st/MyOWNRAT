import builtins
import sys
import tabulate

__HELP_OVERALL__ = """Usage: server.py <mode> [options]

Modes:
  bind       Run the server and wait for connections.

Use server.py <mode> --help for mode specific options."""

__HELP_BIND__ = """Bind mode help:
  -a, --address   Address to bind (default 127.0.0.1)
  -p, --port      Port to bind (required)"""



class Pull:
    WHITE = ''
    PURPLE = ''
    CYAN = ''
    DARKCYAN = ''
    BLUE = ''
    GREEN = ''
    YELLOW = ''
    RED = ''
    BOLD = ''
    UNDERLINE = ''
    END = ''
    LINEUP = ''

    def __init__(self):
        pass

    def get_com(self, mss=None):
        """
        Legge un comando da input.
        Se viene passato un oggetto/session con attributi .ip e .port, mostra [ip:port] nel prompt.
        Accetta sia un singolo oggetto sia una sequenza (lista/tupla) dove l'oggetto è in posizione 1.
        """
        session = None

        if mss is not None:
            # se è direttamente un oggetto sessione
            if hasattr(mss, "ip") and hasattr(mss, "port"):
                session = mss
            # se è una lista/tupla, mantengo la semantica originale con indice 1
            elif isinstance(mss, (list, tuple)) and len(mss) > 1:
                candidate = mss[1]
                if hasattr(candidate, "ip") and hasattr(candidate, "port"):
                    session = candidate

        if session is not None:
            prompt = (
                self.DARKCYAN + "$" + self.END + " ["
                + self.GREEN + str(session.ip) + self.END + ":"
                + self.RED + str(session.port) + self.END + "] "
            )
        else:
            prompt = self.DARKCYAN + "$" + self.END + " "

        rtval = builtins.input(prompt)
        rtval = rtval.strip()
        return rtval

    def print(self, mess):
        builtins.print(
            self.GREEN + "[" + self.UNDERLINE + "*" + self.END + self.GREEN + "] "
            + self.END + str(mess) + self.END
        )

    def error(self, mess):
        builtins.print(
            self.RED + "[" + self.UNDERLINE + "!" + self.END + self.RED + "] "
            + self.END + str(mess) + self.END
        )

    def exit(self, mess=""):
        sys.exit(
            self.RED + "[" + self.UNDERLINE + "~" + self.END + self.RED + "] "
            + self.END + str(mess) + self.END
        )

    def help_c_current(self):
        headers = (
            self.BOLD + 'Command' + self.END,
            self.BOLD + 'Description' + self.END
        )
        lister = [
            ('help', 'Shows manual for commands'),
            ('sessions', 'Show all connected clients to the server'),
            ('connect', 'Connect to a Specific Client'),
            ('disconnect', 'Disconnect from Current Client'),
            ('clear', 'Clear Screen'),
            ('shell', 'Launch a New Terminal/Shell.'),
            ('keylogger', 'KeyLogger Module'),
            ('sysinfo', 'Dump System, Processor, CPU and Network Information'),
            ('screenshot', 'Take Screenshot on Target Machine and Save on Local'),
            ('exit', 'Exit from RAT')
        ]
        sys.stdout.write("\n")
        builtins.print(tabulate.tabulate(lister, headers=headers))
        sys.stdout.write("\n")

    def help_c_general(self):
        headers = (
            self.BOLD + 'Command' + self.END,
            self.BOLD + 'Description' + self.END
        )
        lister = [
            ('help', 'Shows manual for commands'),
            ('sessions', 'Show all connected clients to the server'),
            ('connect', 'Connect to a Specific Client'),
            ('disconnect', 'Disconnect from Current Client'),
            ('clear', 'Clear Screen'),
            ('exit', 'Exit from RAT')
        ]
        sys.stdout.write("\n")
        builtins.print(tabulate.tabulate(lister, headers=headers))
        sys.stdout.write("\n")

    def help_c_sessions(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Display connected sessions to the server!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ sessions")
        sys.stdout.write("\n")

    def help_c_connect(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Connect to an available session!")
        builtins.print("Arguments  : Session ID")
        builtins.print("Example    : \n")
        builtins.print("$ connect 56\n")
        headers = (
            self.BOLD + 'Argument' + self.END,
            self.BOLD + 'Type' + self.END,
            self.BOLD + 'Description' + self.END
        )
        lister = [
            ('ID', 'integer', 'ID of the sessions from the list')
        ]
        builtins.print(tabulate.tabulate(lister, headers=headers))
        sys.stdout.write("\n")

    def help_c_disconnect(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Disconnect current session!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ disconnect")
        sys.stdout.write("\n")

    def help_c_clear(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Clear screen!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ clear")
        sys.stdout.write("\n")

    def help_c_shell(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Launch a shell against client!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ shell")
        sys.stdout.write("\n")

    def help_c_keylogger(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Keylogger Module!")
        builtins.print("Arguments  : on, off, dump")
        builtins.print("Example    : \n")
        builtins.print("$ keylogger on")
        builtins.print("$ keylogger off")
        builtins.print("$ keylogger dump\n")
        headers = (
            self.BOLD + 'Argument' + self.END,
            self.BOLD + 'Description' + self.END
        )
        lister = [
            ('on', 'Turn Keylogger on'),
            ('off', 'Turn Keylogger off'),
            ('dump', 'Dump keylogs')
        ]
        builtins.print(tabulate.tabulate(lister, headers=headers))
        sys.stdout.write("\n")

    def help_c_sysinfo(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Gathers system information!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ sysinfo")
        sys.stdout.write("\n")

    def help_c_screenshot(self):
        sys.stdout.write("\n")
        builtins.print("Info       : Screenshot the current screen and save it on server!")
        builtins.print("Arguments  : None")
        builtins.print("Example    : \n")
        builtins.print("$ screenshot")
        sys.stdout.write("\n")

    def help_overall(self):
        builtins.print(__HELP_OVERALL__)
        sys.exit(0)

    def help_bind(self):
        builtins.print(__HELP_BIND__)
        sys.exit(0)

    def help_help(self):
        builtins.print("Use --help for mode specific assistance.")
        sys.exit(0)


pull = Pull()

# expose attributes/functions at module level for convenience
WHITE = pull.WHITE
PURPLE = pull.PURPLE
CYAN = pull.CYAN
DARKCYAN = pull.DARKCYAN
BLUE = pull.BLUE
GREEN = pull.GREEN
YELLOW = pull.YELLOW
RED = pull.RED
BOLD = pull.BOLD
UNDERLINE = pull.UNDERLINE
END = pull.END
LINEUP = pull.LINEUP

get_com = pull.get_com
print = pull.print
error = pull.error
exit = pull.exit
help_c_current = pull.help_c_current
help_c_general = pull.help_c_general
help_c_sessions = pull.help_c_sessions
help_c_connect = pull.help_c_connect
help_c_disconnect = pull.help_c_disconnect
help_c_clear = pull.help_c_clear
help_c_shell = pull.help_c_shell
help_c_keylogger = pull.help_c_keylogger
help_c_sysinfo = pull.help_c_sysinfo
help_c_screenshot = pull.help_c_screenshot
help_overall = pull.help_overall
help_bind = pull.help_bind
help_help = pull.help_help
