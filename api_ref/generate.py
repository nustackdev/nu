from pprint import pprint

from loomiverse.pydoc_nextra.config import load_config_from_file
from loomiverse.pydoc_nextra.generator import DocumentationGenerator
from loomiverse.pydoc_nextra.logger import setup_logger

logger = setup_logger(
    name="loomiverse.pydoc_nextra",
    level=10,
    log_file=None,
    console=True,
)

if __name__ == "__main__":
    # Load the configuration from the file
    config = load_config_from_file("config.yaml")

    # Print the loaded configuration
    logger.info("Loaded configuration:")
    pprint(config)

    # Create a DocumentationGenerator instance
    logger.info("Creating DocumentationGenerator instance...")
    generator = DocumentationGenerator(config)
    logger.info("DocumentationGenerator instance created.")

    # Generate the documentation
    logger.info("Generating documentation...")
    generator.generate()
    logger.info("Documentation generation completed.")
