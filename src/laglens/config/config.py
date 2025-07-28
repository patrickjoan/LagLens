BINDINGS = [
    ("q", "quit", "Quit"),
    ("s", "save_statistics", "Save Stats"),
    ("n", "focus_add_server", "Add Server"),
    ("c", "clear_form", "Clear Form"),
]

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "laglens.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
