import shutil
from pathlib import Path

from loomiverse.pydoc_nextra.config import load_config_from_file
from loomiverse.pydoc_nextra.logger import setup_logger

logger = setup_logger(
    name="loomiverse.pydoc_nextra",
    level=10,
    log_file=None,
    console=True,
)

if __name__ == "__main__":
    # Check if the script is being run from the correct directory
    current_path = Path(__file__).resolve()
    current_parent = current_path.parent
    scripts_dir = current_parent.parent
    docs_dir = scripts_dir.parent
    loomi_dir = docs_dir.parent

    if loomi_dir.name != "loomi":
        raise RuntimeError(
            f"Script must be run from the 'loomi/docs/scripts/api_ref' directory. Current path: {current_path}"
        )

    config_file_paths = [
        "loomi_config.yaml",
        "loomistd_config.yaml",
    ]

    for config_file_path in config_file_paths:
        # Load the configuration from the file
        config = load_config_from_file(config_file_path)

        # Set absolute paths for source_dir and output_dir
        config.discovery.source_dir = loomi_dir / config.discovery.source_dir
        config.output.output_dir = loomi_dir / config.output.output_dir

        # Remove existing output directory if it exists
        api_ref_dir = config.output.output_dir / config.meta.name
        if api_ref_dir.exists():
            logger.info(f"Removing existing output directory: {api_ref_dir}")
            shutil.rmtree(api_ref_dir.resolve())

    # Remove meta files
    navigation_file = config.output.output_dir / "_meta.js"
    navigation_file.unlink(missing_ok=True)
