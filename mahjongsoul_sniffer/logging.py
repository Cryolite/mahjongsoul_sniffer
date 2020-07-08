#!/usr/bin/env python3

import logging
import logging.handlers
import mahjongsoul_sniffer.config


log_format = '%(asctime)s:%(filename)s:%(funcName)s:%(lineno)d:%(levelname)s:\
 %(message)s'
config = mahjongsoul_sniffer.config.config
log_handler = logging.handlers.RotatingFileHandler(
    filename=config.log_file_path, maxBytes=config.log_file_max_bytes,
    backupCount=config.log_file_backup_count, delay=True)
logging.basicConfig(format=log_format, level=config.logging_level,
                    handlers=[log_handler])
