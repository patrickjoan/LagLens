import os
import sys

# Add the src directory to the Python path for direct execution
if __name__ == "__main__":
    # Get the directory containing this file (src/laglens/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the src directory (parent of laglens)
    src_dir = os.path.dirname(current_dir)
    # Add src to Python path if not already there
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

# Now we can use absolute imports that work both ways
from laglens.app import LagLensApp
from laglens.config.config import (
    LOG_BACKUP_COUNT,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    LOG_MAX_SIZE,
)
from laglens.logger import get_logger, setup_logging


def main():
    """Main entry point for the LagLens application."""
    setup_logging(
        log_level=LOG_LEVEL,
        log_file=LOG_FILE,
        log_format=LOG_FORMAT,
        max_size=LOG_MAX_SIZE,
        backup_count=LOG_BACKUP_COUNT,
    )
    logger = get_logger("main")

    try:
        logger.info("Starting LagLens application")
        app = LagLensApp()
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running application: {e}", exc_info=True)
        print(f"Error running application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
