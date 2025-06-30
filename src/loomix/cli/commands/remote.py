import signal
import sys
from pathlib import Path
from typing import Optional

import rich_click as click

from loomistd.remote import RPyCTCPServer, RPyCTCPServerSpec, RPyCUnixServer, RPyCUnixServerSpec


@click.command(name="remote")
@click.option(
    "--type",
    "server_type",
    type=click.Choice(["tcp", "unix"], case_sensitive=False),
    default="tcp",
    help="Server connection type (tcp or unix socket)",
)
@click.option(
    "--host",
    default="localhost",
    help="Host address for TCP server (ignored for unix sockets)",
)
@click.option(
    "--port",
    type=int,
    default=18812,
    help="Port number for TCP server (ignored for unix sockets)",
)
@click.option(
    "--socket-path",
    type=click.Path(),
    default="/tmp/loomi_rpyc.sock",
    help="Path for Unix socket file (ignored for TCP)",
)
@click.option(
    "--auto-register",
    is_flag=True,
    default=False,
    help="Enable auto-registration with RPyC registry",
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Request timeout in seconds",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging",
)
@click.option(
    "--log-dir",
    type=click.Path(),
    default=".logs",
    help="Directory for log files",
)
@click.option(
    "--log-level",
    type=int,
    default=20,
    help="Log level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR)",
)
def remote(  # noqa: C901
    server_type: str,
    host: str,
    port: int,
    socket_path: str,
    auto_register: bool,
    timeout: int,
    verbose: bool,
    log_dir: str,
    log_level: int,
):
    """
    Start a Loomi RPyC server for remote resource access.

    This command starts an RPyC server that can host Loomi resources remotely,
    allowing clients to connect and access resources over the network or Unix sockets.

    Examples:
        # Start TCP server on default port
        loomix remote

        # Start TCP server on specific host/port
        loomix remote --host 0.0.0.0 --port 8080

        # Start Unix socket server
        loomix remote --type unix --socket-path /tmp/my_app.sock

        # Start with verbose logging
        loomix remote --verbose --log-level 10
    """

    # Setup logging
    try:
        from loomix.logging import setup_logging

        actual_log_level = 10 if verbose else log_level
        setup_logging(log_dir, log_level=actual_log_level)

        if verbose:
            click.echo(f"📋 Logging configured: level={actual_log_level}, dir={log_dir}")

    except ImportError:
        click.echo(
            "⚠️  Logging setup not available, continuing without logging configuration", err=True
        )

    # Create server specification based on type
    if server_type.lower() == "tcp":
        server_spec = RPyCTCPServerSpec(
            bind_address=host,
            bind_port=port,
            auto_register=auto_register,
            config={
                "allow_all_attrs": True,
                "sync_request_timeout": timeout,
            },
        )
        server_cls = RPyCTCPServer
        endpoint_info = f"{host}:{port}"

    elif server_type.lower() == "unix":
        # Validate socket path
        socket_file = Path(socket_path)
        if socket_file.exists():
            click.echo(f"❌ Socket file {socket_path} already exists", err=True)
            click.echo("   Please remove it or choose a different path", err=True)
            sys.exit(1)

        server_spec = RPyCUnixServerSpec(
            socket_path=socket_path,
            auto_register=auto_register,
            config={
                "allow_all_attrs": True,
                "sync_request_timeout": timeout,
            },
        )
        server_cls = RPyCUnixServer
        endpoint_info = socket_path

    else:
        click.echo(f"❌ Unsupported server type: {server_type}", err=True)
        sys.exit(1)

    # Display startup information
    click.echo(f"🚀 Starting {server_type.upper()} RPyC server...")
    click.echo(f"📡 Endpoint: {endpoint_info}")

    if verbose:
        click.echo("⚙️  Configuration:")
        click.echo(f"   - Auto-register: {auto_register}")
        click.echo(f"   - Timeout: {timeout}s")
        click.echo(f"   - Server type: {server_type.upper()}")

        if server_type.lower() == "unix":
            click.echo(f"   - Socket path: {socket_path}")
        else:
            click.echo(f"   - Host: {host}")
            click.echo(f"   - Port: {port}")

    # Setup signal handlers for graceful shutdown
    server_instance: Optional[RPyCTCPServer | RPyCUnixServer] = None

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        click.echo(f"\n🛑 Received signal {signum}, shutting down server...")
        if server_instance and server_instance.active:
            server_instance.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Create and start server
        with server_cls(server_spec) as server:
            server_instance = server

            click.echo("✅ Server initialized successfully")
            click.echo(f"🔗 Clients can connect to: {endpoint_info}")
            click.echo("📊 Press Ctrl+C to stop server")

            if verbose:
                click.echo(f"🔍 Server active: {server.active}")

            # Start the server
            server.start()

            # Keep server running until interrupted
            try:
                while server.active:
                    # Check server status periodically
                    import time

                    time.sleep(1)

            except KeyboardInterrupt:
                click.echo("\n🛑 Keyboard interrupt received...")

    except Exception as e:
        click.echo(f"❌ Failed to start server: {e}", err=True)

        # Clean up socket file if it was created
        if server_type.lower() == "unix":
            socket_file = Path(socket_path)
            if socket_file.exists():
                try:
                    socket_file.unlink()
                    if verbose:
                        click.echo(f"🧹 Cleaned up socket file: {socket_path}")
                except Exception as cleanup_error:
                    click.echo(f"⚠️  Failed to clean up socket file: {cleanup_error}", err=True)

        sys.exit(1)

    finally:
        click.echo("🏁 Server stopped")

        # Final cleanup for Unix sockets
        if server_type.lower() == "unix":
            socket_file = Path(socket_path)
            if socket_file.exists():
                try:
                    socket_file.unlink()
                    if verbose:
                        click.echo(f"🧹 Cleaned up socket file: {socket_path}")
                except Exception as cleanup_error:
                    click.echo(f"⚠️  Failed to clean up socket file: {cleanup_error}", err=True)
