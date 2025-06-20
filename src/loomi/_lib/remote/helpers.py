"""
Helper functions for creating remote connections.

This module provides convenient functions for creating connection factories
for common scenarios like RPyC over TCP or Unix sockets.
"""

from typing import Any, Callable, Optional

__all__ = [
    "rpyc_tcp",
    "rpyc_unix",
    "create_rpyc_connection",
]


def rpyc_tcp(host: str = "localhost", port: int = 18861, **rpyc_config) -> Callable[[], Any]:
    """
    Create RPyC TCP connection factory.

    Args:
        host: Server hostname
        port: Server port
        **rpyc_config: Additional RPyC configuration

    Returns:
        Connection factory function

    Example:
        >>> connection_factory = rpyc_tcp("myserver", 8080)
        >>> spec = StateSpec().as_remote(connection_factory)
    """

    def factory():
        import rpyc

        # Default config
        config = {
            "allow_all_attrs": True,
            "sync_request_timeout": 30,
        }
        config.update(rpyc_config)

        return rpyc.connect(host, port, config=config)

    return factory


def rpyc_unix(socket_path: str, **rpyc_config) -> Callable[[], Any]:
    """
    Create RPyC Unix socket connection factory.

    Args:
        socket_path: Path to Unix socket
        **rpyc_config: Additional RPyC configuration

    Returns:
        Connection factory function

    Example:
        >>> connection_factory = rpyc_unix("/tmp/service.sock")
        >>> spec = StateSpec().as_remote(connection_factory)
    """

    def factory():
        import rpyc
        from rpyc.core.stream import SocketStream

        # Default config
        config = {
            "allow_all_attrs": True,
            "sync_request_timeout": 30,
        }
        config.update(rpyc_config)

        stream = SocketStream.unix_connect(socket_path)
        return rpyc.connect_stream(stream, config=config)

    return factory


def create_rpyc_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    socket_path: Optional[str] = None,
    **rpyc_config,
) -> Callable[[], Any]:
    """
    Create RPyC connection factory with auto-detection.

    Args:
        host: Server hostname (for TCP)
        port: Server port (for TCP)
        socket_path: Unix socket path (takes precedence)
        **rpyc_config: Additional RPyC configuration

    Returns:
        Connection factory function

    Raises:
        ValueError: If neither socket_path nor host/port provided

    Example:
        >>> # TCP connection
        >>> factory = create_rpyc_connection(host="server", port=8080)
        >>>
        >>> # Unix socket connection
        >>> factory = create_rpyc_connection(socket_path="/tmp/service.sock")
    """
    if socket_path:
        return rpyc_unix(socket_path, **rpyc_config)
    elif host and port:
        return rpyc_tcp(host, port, **rpyc_config)
    else:
        raise ValueError("Must provide either socket_path or host/port")
