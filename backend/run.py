from app import create_app

app = create_app()

if __name__ == "__main__":
    import socket
    from pathlib import Path

    host = "0.0.0.0"
    preferred_port = int(app.config.get("PORT") or 5001)
    debug = bool(app.config.get("DEBUG"))

    def _port_is_free(port: int) -> bool:
        # Prefer a connect probe: on macOS, bind checks can be misleading depending on socket options.
        try:
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.settimeout(0.2)
            in_use = c.connect_ex(("127.0.0.1", port)) == 0
            c.close()
            if in_use:
                return False
        except Exception:
            pass

        # Fallback: try binding without SO_REUSEADDR.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False
        finally:
            try:
                s.close()
            except Exception:
                pass

    port = preferred_port
    if not _port_is_free(port):
        # Avoid "Address already in use" by selecting the next available port.
        for candidate in range(preferred_port + 1, preferred_port + 51):
            if _port_is_free(candidate):
                port = candidate
                break

    if port != preferred_port:
        print(f"Port {preferred_port} is in use. Starting on port {port} instead.")

    # Let the frontend dev server auto-target the active backend port.
    try:
        Path(__file__).resolve().parent.joinpath(".runtime-port").write_text(str(port))
    except Exception:
        pass

    # In debug, the reloader starts a second process; that can re-run port selection
    # and surprise you. Keep debug mode, but disable the reloader for predictability.
    app.run(host=host, port=port, debug=debug, use_reloader=False)
