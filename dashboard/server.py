#!/usr/bin/env python3
"""Servidor HTTP para o dashboard CAGED CE (local e Railway)."""

import http.server
import os
import socket
import socketserver
import sys
import webbrowser
from pathlib import Path

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8765"))
DIR = Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def log_message(self, format, *args):
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def encontrar_porta(host, portas):
    """Tenta portas alternativas; usa porta livre do sistema se necessario."""
    for porta in portas:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, porta))
            sock.close()
            return porta
        except OSError:
            continue

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, 0))
    porta = sock.getsockname()[1]
    sock.close()
    return porta


def main():
    host = HOST
    portas_fallback = [PORT, 8765, 8888, 9090, 5500, 8081, 8080]
    porta = PORT if host != "127.0.0.1" else encontrar_porta(host, portas_fallback)

    try:
        httpd = ReusableTCPServer((host, porta), Handler)
    except OSError as err:
        print(f"ERRO: nao foi possivel iniciar o servidor ({err})", file=sys.stderr)
        sys.exit(1)

    url = f"http://{'localhost' if host == '0.0.0.0' else host}:{porta}/"
    print("=" * 50)
    print("  Dashboard CAGED - Ceara")
    print("=" * 50)
    print(f"  Servidor: {url}")
    if host == "127.0.0.1" and porta != portas_fallback[0]:
        print(f"  (porta {portas_fallback[0]} indisponivel; usando {porta})")
    print("  Pressione Ctrl+C para encerrar")
    print("=" * 50)

    if host == "127.0.0.1" and not os.environ.get("RAILWAY_ENVIRONMENT"):
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
