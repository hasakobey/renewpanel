"""Ortak SSH baglantisi.

Kimlik bilgisi RENEW_SSH_HOST / RENEW_SSH_USER / RENEW_SSH_PASSWORD ortam
degiskenlerinden okunur. Parola hicbir zaman ekrana yazilmaz veya koda
gomulmez; .env dosyasi ya da kabuk ortam degiskeni kullanilir.
"""
import os
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parent


def _creds_from_env():
    host = os.environ.get("RENEW_SSH_HOST")
    user = os.environ.get("RENEW_SSH_USER")
    pwd = os.environ.get("RENEW_SSH_PASSWORD")
    if not (host and user and pwd):
        raise RuntimeError(
            "RENEW_SSH_HOST / RENEW_SSH_USER / RENEW_SSH_PASSWORD ortam "
            "degiskenleri tanimli degil (.env dosyasina bakin)."
        )
    return (host,), {"username": user, "password": pwd, "timeout": 25}


def ssh():
    args, kwargs = _creds_from_env()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(*args, **kwargs)
    return client


def run(client, cmd, timeout=900, check=True):
    _, out, err = client.exec_command(cmd, timeout=timeout)
    stdout = out.read().decode("utf-8", errors="replace")
    stderr = err.read().decode("utf-8", errors="replace")
    code = out.channel.recv_exit_status()
    if check and code:
        raise RuntimeError(f"exit {code}: {cmd}\n{stdout}\n{stderr}")
    return code, stdout, stderr
