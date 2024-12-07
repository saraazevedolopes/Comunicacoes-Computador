import logging
log_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL, logging.FATAL]
    
def server_console(level=logging.DEBUG):
    logger = logging.getLogger(0)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_levels[int(level)])
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

# Function to set up a logger
def setup_logger(name, log_file, server, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler for writing logs to a file
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)

    # Formatter for log messages
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)
    
    if not server:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_levels[level])
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


















    