import sys

from app import LagLensApp
from config.config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT
from logger import get_logger, setup_logging


def main():
    """Main entry point for the LagLens application."""
    # Setup logging with configuration
    setup_logging(
        log_level=LOG_LEVEL, 
        log_file=LOG_FILE,
        log_format=LOG_FORMAT,
        max_size=LOG_MAX_SIZE,
        backup_count=LOG_BACKUP_COUNT
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

