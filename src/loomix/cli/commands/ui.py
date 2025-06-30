import os
import subprocess

import rich_click as click


@click.command(name="ui")
@click.option("dir", "--dir", type=click.Path(exists=True), required=True, help="Path to the dir.")
def ui(dir):
    """
    Start the Loomix dashboard.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_file_path = os.path.join(current_dir, os.pardir, "ui", "run.py")
    command = ["streamlit", "run", ui_file_path, "--", "--dir", dir]

    try:
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        ) as process:
            # Real-time output
            for line in process.stdout:  # type: ignore
                click.echo(line, nl=False)

            # Check for any errors
            for line in process.stderr:  # type: ignore
                click.echo(line, nl=False, err=True)

            # Wait for the process to complete
            process.wait()

            if process.returncode != 0:
                click.echo(f"Streamlit app exited with code {process.returncode}", err=True)
    except KeyboardInterrupt:
        click.echo("\nStreamlit app stopped.")
