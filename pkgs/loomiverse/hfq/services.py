from __future__ import annotations

import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import attrs

from loomi import ResourceSpec, SyncService


class DataStream(SyncService):
    """
    Data ingestion service that processes and stores data.

    This service is responsible for ingesting data, processing it, and storing the results.
    It can be extended to implement specific data processing logic.
    """

    def get_candle(self):
        # Generate random candle data
        timestamp = time.time()
        open_price = round(random.uniform(100, 200), 2)
        high_price = round(open_price * random.uniform(1, 1.05), 2)
        low_price = round(open_price * random.uniform(0.95, 1), 2)
        close_price = round(random.uniform(low_price, high_price), 2)
        volume = round(random.uniform(1000, 10000), 2)

        return {
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        }


@attrs.define(frozen=True, slots=True, kw_only=True)
class DataStreamSpec(ResourceSpec):
    """
    Specification for the HFQ application.

    This spec defines the application and its resources.
    """

    name: str = "DataStream"
    factory: type[DataStream] = DataStream


class UIService(SyncService):
    """
    UIService implementation that runs Dash UI in a separate process.
    """

    spec: UIServiceSpec

    @property
    def script_path(self) -> Path:
        """Path to the temporary script file."""
        return (
            Path(self.spec.script_path)
            if isinstance(self.spec.script_path, str)
            else self.spec.script_path
        )

    def setup(self):
        """Start the UI process."""
        self._process: Optional[subprocess.Popen] = None

        try:
            # Start the UI process
            self._process = subprocess.Popen(
                [sys.executable, str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                env=os.environ.copy(),
            )

            time.sleep(1)

            # Check if process started successfully
            if self._process.poll() is not None:
                # Process has already terminated
                stdout, stderr = self._process.communicate()
                raise RuntimeError(
                    f"UI process failed to start. "
                    f"Return code: {self._process.returncode}\n"
                    f"STDOUT: {stdout.decode()}\n"
                    f"STDERR: {stderr.decode()}"
                )

        except Exception as e:
            self.cleanup()  # Clean up any partial setup
            raise RuntimeError(f"Failed to start UI service: {e}")

    def cleanup(self):
        """Stop the UI process and clean up resources."""
        # Terminate the process if it's running
        if self._process is not None:
            try:
                if self._process.poll() is None:  # Process is still running
                    print(f"🛑 Terminating UI process (PID: {self._process.pid})")
                    self._process.terminate()

                    # Wait for graceful shutdown
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful shutdown fails
                        print("⚠️ Force killing UI process")
                        self._process.kill()
                        self._process.wait()

                print("✅ UI process stopped")
            except Exception as e:
                print(f"⚠️ Error stopping UI process: {e}")
            finally:
                self._process = None


@attrs.define(frozen=True, slots=True, kw_only=True)
class UIServiceSpec(ResourceSpec):
    """UI Service specification."""

    name: str = "ui"
    factory: type = UIService
    script_path: Path | str
