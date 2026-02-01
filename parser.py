import pull


class PARSER:

    COMMANDS = ['bind']

    def __init__(self, prs):
        self.mode = self.v_mode(prs.mode, prs.help)
        self.help = self.v_help(prs.help)

        if self.mode == "bind":
            self.address = self.v_address(prs.address)
            self.port = self.v_port(prs.port)

    def v_help(self, hl):
        if hl:
            if not self.mode:
                pull.help_overall()
            else:
                if self.mode == "bind":
                    pull.help_bind()
                else:
                    pull.help_help()

    def v_address(self, str):
        return str

    def v_port(self, port):
        if not port:
            pull.exit("You need to Supply a Valid Port Number")

        if port <= 0 or port > 65535:
            pull.exit("Invalid Port Number")

        return port

    def v_mode(self, val, hl):
        if val:
            if val in self.COMMANDS:
                return val
            else:
                pull.exit("No such command found in database")
        else:
            if not hl:
                pull.exit("Invalid Syntax. Refer to the manual!")
