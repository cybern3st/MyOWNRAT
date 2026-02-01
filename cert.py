#!/usr/bin/env python3
import argparse
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile


def run_openssl(args: list[str]) -> None:
    try:
        subprocess.run(["openssl", *args], check=True)
    except FileNotFoundError as exc:
        raise SystemExit("OpenSSL is required but was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"OpenSSL command failed: {' '.join(exc.cmd)}") from exc


def ensure_permissions(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError:
        pass


def create_ca(cert_dir: Path, subject: str, days: int) -> None:
    ca_key = cert_dir / "ca.key"
    ca_cert = cert_dir / "ca.crt"

    if not ca_key.exists():
        run_openssl(["genrsa", "-out", str(ca_key), "4096"])
        ensure_permissions(ca_key, 0o600)

    if not ca_cert.exists():
        run_openssl(
            [
                "req",
                "-x509",
                "-new",
                "-nodes",
                "-key",
                str(ca_key),
                "-sha256",
                "-days",
                str(days),
                "-out",
                str(ca_cert),
                "-subj",
                subject,
            ]
        )


def create_server_cert(cert_dir: Path, subject: str, days: int) -> None:
    ca_key = cert_dir / "ca.key"
    ca_cert = cert_dir / "ca.crt"
    server_key = cert_dir / "server.key"
    server_csr = cert_dir / "server.csr"
    server_cert = cert_dir / "server.crt"

    if not server_key.exists():
        run_openssl(["genrsa", "-out", str(server_key), "2048"])
        ensure_permissions(server_key, 0o600)

    config = """
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
""".strip()

    with NamedTemporaryFile(mode="w", delete=False) as tmp:
        tmp.write(config)
        tmp_path = tmp.name

    try:
        if not server_csr.exists() or not server_cert.exists():
            run_openssl(
                [
                    "req",
                    "-new",
                    "-key",
                    str(server_key),
                    "-out",
                    str(server_csr),
                    "-subj",
                    subject,
                    "-config",
                    tmp_path,
                ]
            )

        if not server_cert.exists():
            run_openssl(
                [
                    "x509",
                    "-req",
                    "-in",
                    str(server_csr),
                    "-CA",
                    str(ca_cert),
                    "-CAkey",
                    str(ca_key),
                    "-CAcreateserial",
                    "-out",
                    str(server_cert),
                    "-days",
                    str(days),
                    "-sha256",
                    "-extfile",
                    tmp_path,
                    "-extensions",
                    "v3_req",
                ]
            )
    finally:
        os.unlink(tmp_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create self-signed CA and server certificates for MyOWNRAT."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=825,
        help="Validity in days for generated certificates.",
    )
    parser.add_argument(
        "--ca-subject",
        default="/C=US/ST=State/L=City/O=MyOWNRAT/OU=Dev/CN=MyOWNRAT-CA",
        help="Subject for the CA certificate.",
    )
    parser.add_argument(
        "--server-subject",
        default="/C=US/ST=State/L=City/O=MyOWNRAT/OU=Dev/CN=localhost",
        help="Subject for the server certificate.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    cert_dir = base_dir / "certs"
    cert_dir.mkdir(exist_ok=True)

    create_ca(cert_dir, args.ca_subject, args.days)
    create_server_cert(cert_dir, args.server_subject, args.days)

    print(f"Certificates ready in: {cert_dir}")
    print("- ca.crt / ca.key")
    print("- server.crt / server.key")


if __name__ == "__main__":
    main()
