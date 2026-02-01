# MyOWNRAT

MyOWNRAT is a console-based remote administration tool that offers a primary mode:

* **bind** — starts the server, accepts connections from remote clients, and provides an interactive console for issuing commands.

This document walks through every module and function to explain how the tool fits together and how to operate it safely.

## Table of contents
1. [Project layout](#project-layout)
2. [Prerequisites](#prerequisites)
3. [Safety and legal notice](#safety-and-legal-notice)

4. [Linux setup](#linux-setup)
5. [CLI usage](#cli-usage)
6. [Server workflow (bind mode)](#server-workflow-bind-mode)
7. [Console commands](#console-commands)
8. [Module reference](#module-reference)
9. [Development notes](#development-notes)
9. [Dependencies](#dependencies)
10. [Development notes](#development-notes)


## Project layout

| File | Purpose |
| --- | --- |
| `server.py` | Entry point that parses CLI flags, shows the banner, and dispatches to bind mode. |
| `server.py` | Entry point that parses CLI flags and dispatches to bind mode. |
| `parser.py` | Validates command-line arguments for bind mode and produces a structured configuration object. |
| `interface.py` | Manages the listening socket, accepts client connections, and routes console commands. |
| `commcenter.py` | Implements the interactive command set used while the server is running. |
| `client.py` | Represents a connected client session and handles the lightweight message protocol. |
| `pull.py` | Shared utilities for colored output, prompts, logo/help text, and convenience wrappers. |
| `pull.py` | Shared utilities for prompts, help text, and convenience wrappers. |

## Prerequisites

* Python 3.9+ is recommended for the server.
* The client functionality is designed for Windows; running on other operating systems may limit features such as screenshot capture or scheduled task setup.
* The server and client will create directories such as `tmp/`, `screenshots/`, and `keylogs/` at runtime, so ensure the working directory is writable.

## Safety and legal notice

This project is a remote administration tool intended for educational, testing, and authorized administration scenarios. Use it only on systems you own or have explicit permission to manage. Running it against systems without consent may be illegal and could violate organizational policies. Review local laws and obtain written authorization before using the tool in any real environment.


## Linux setup

1. **Clone the repository**
   ```
   git clone https://github.com/cybern3st/MyOWNRAT
   cd MyOWNRAT
   ```
2. **Create a virtual environment (recommended)**
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Run the tool**
   ```
   python server.py bind -a 0.0.0.0 -p 4444
   ```

## CLI usage
By default, the script writes `cert.pem` and `key.pem` alongside the script. If
2. `INTERFACE.bind()` opens the TCP socket; `INTERFACE.accept()` spawns a background thread to accept incoming clients and register them.
3. `INTERFACE.launch()` presents an interactive prompt. You can list sessions, connect to one, and execute commands like `shell`, `sysinfo`, `keylogger`, and `screenshot`.
4. Exiting the interface (`exit`) tears down the socket via `INTERFACE.close()`.

## Console commands

The console prompt changes depending on whether a client session is active. Key commands provided by `COMMCENTER`:

| Command | Description |
| --- | --- |
| `help` | Show general help; `help <command>` provides command-specific details. |
| `sessions` | List connected clients with IDs, IPs, ports, and status. |
| `connect <id>` | Select a client session by ID. |
| `disconnect` | Clear the current session selection. |
| `clear` | Clear the terminal. |
| `shell` | Open a remote shell against the selected client. Type `exit` (after the `shell:` prefix is added automatically) to close it. |
| `keylogger on|off|dump` | Control or retrieve keylogger data from the client. `dump` saves logs under `keylogs/<client_ip>/`. |
| `sysinfo` | Request system information from the client and display it. |
| `screenshot` | Capture the client screen and save it under `screenshots/<client_ip>/`. |
| `exit` | Quit the server process. |

## Module reference

### `server.py`
* **`build_parser()`** — Defines CLI arguments without auto-added help so custom help handling can be used.
* **`main()`** — Shows the ASCII logo, parses arguments, initializes `PARSER`, and dispatches to `INTERFACE` (bind). Ensures sockets are closed when the interface exits.
* **`main()`** — Parses arguments, initializes `PARSER`, and dispatches to `INTERFACE` (bind). Ensures sockets are closed when the interface exits.

### `parser.py`
* **`PARSER`** — Validates mode selection and arguments. On validation errors, calls into `pull.exit()` with descriptive messages. Provides attributes: `mode`, `address`, `port`.
* **`v_help()`** — Routes `-h/--help` handling to the appropriate help text in `pull`.
* **`v_mode()`** — Accepts only `bind`; otherwise exits with an error.
* **`v_port()`** — Ensures the port is provided and within 1–65535.

### `interface.py`
* **`INTERFACE`** — Extends `COMMCENTER` and stores the configured address/port.
  * `bind()` — Creates and binds a TCP socket; reports success or exits on failure.
  * `accept()` — Starts a daemon thread running `accept_threads()` to accept and register clients.
  * `accept_threads()` — Accept loop that wraps raw sockets into `CLIENT` objects, starts their receive threads, and tracks them with incremental IDs.
  * `launch()` — Displays a startup message and enters the command loop; delegates command parsing to `execute()`.
  * `execute(vals)` — Dispatches parsed command tokens to the appropriate `COMMCENTER` handlers.
  * `close()` — Closes the listening socket.

### `commcenter.py`
* Provides the interactive command implementations listed in [Console commands](#console-commands).
* Maintains state:
  * `CLIENTS` — list of `(id, CLIENT)` tuples for all connected sessions.
  * `COUNTER` — incrementing ID counter.
  * `CURRENT` — currently selected `(id, CLIENT)` tuple, or empty when none.
* Handles per-command help (`c_help`) and lookup of session IDs (`get_valid`).
* Commands like `c_keylogger`, `c_screenshot`, and `c_sysinfo` format requests, receive data from the active `CLIENT`, and persist artifacts under descriptive directories when needed.

### `client.py`
* **`CLIENT`** — Represents a connected remote host.
  * `engage()` — Starts a background thread to receive messages via `acceptor()`.
  * `acceptor()` — Reads data from the socket, detects message boundaries using the sentinel `KEY` (`#@JEBUN@#`), decodes Base64 payloads, and stores the latest message.
  * `send_data(val)` — Base64-encodes an outgoing string, appends `KEY`, and sends it to the client.
  * `recv_data()` — Busy-waits until a complete message is available, then returns it and resets the buffer.

### `pull.py`
* Houses shared color codes, ASCII logo, and help text strings.
* **`Pull` class** configures color support and exposes helpers:
  * `logo()` — prints the banner.
* Houses prompt formatting and help text strings used by the server console.
* **`Pull` class** exposes helpers:
  * `get_com()` — prompts the user, including current client context when selected.
  * `print()`, `function()`, `error()`, `exit()` — formatted output helpers; `exit()` terminates the program.
  * `print()`, `error()`, `exit()` — output helpers; `exit()` terminates the program.
  * `help_*()` — emit general and mode-specific help plus command-specific descriptions.
* Module-level aliases (e.g., `pull.print`, `pull.RED`) provide convenient imports across the project.
* Module-level aliases (e.g., `pull.print`) provide convenient imports across the project.

## Dependencies

Install external Python packages from the provided requirements file:

```
pip install -r requirements.txt
```

These dependencies are required for features like tabulated console output, TLS crypto utilities, and client screenshots.

## Development notes

* The server is synchronous for command handling; heavy operations on the client side should avoid blocking the communication thread.
* The `CLIENT.recv_data()` loop busy-waits; if you extend it, consider adding a small sleep or synchronization primitive to reduce CPU usage.
* Temporary directories (`tmp/`, `screenshots/`, `keylogs/`) are created as needed. Ensure the process has permission to write to the working directory.
* Color output falls back to plain text on unsupported terminals or non-TTY environments.
* Console output is plain text to keep logs portable across environments.
