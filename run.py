import os
import socket

import uvicorn


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def find_available_port(host: str, start_port: int) -> int:
    port = start_port
    while port <= 65535:
        if not is_port_in_use(host, port):
            return port
        port += 1
    raise RuntimeError("No available port found in range 8000-65535")


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    base_port = int(os.getenv("PORT", "8000"))
    port = find_available_port(host, base_port)
    reload_enabled = os.getenv("RELOAD", "true").lower() in {"1", "true", "yes", "on"}

    if port != base_port:
        print(f"Port {base_port} sedang dipakai. Pakai port {port} sebagai fallback.")

    uvicorn.run("app:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
