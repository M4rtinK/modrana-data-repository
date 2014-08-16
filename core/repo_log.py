#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository - core - logging
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------

SUMMARY_LOG = "summary.log"
SOURCE_LOG = "source.log"
PROCESSING_LOG = "processing.log"
PACKAGING_LOG = "packaging.log"
PUBLISHING_LOG = "publishing.log"

import logging
import os

from . import utils

def init_logging(log_folder_path):
    """Initialize logging for the repository update
    Logging is quite important as a full global update can take many hours and
    be totally unattended (run from cron, etc.), so if something goes wrong we
    need to be able to find out what went wrong.

    :param str log_folder_path: path to the folder where the logs should be stored
    """
    # first try to make sure the logging folder actually exists
    if not utils.createFolderPath(log_folder_path):
        print("ERROR: failed to create logging folder in: %s" % log_folder_path)
        return
    else:
        print("initializing logging")

    # create main logger for the repo update
    logger = logging.getLogger('repo')
    logger.setLevel(logging.DEBUG)

    # create a summary logger that logs everything
    # (this is mainly done so that we can easily correlate
    #  what happened when during the repository update)
    summary_file_log = logging.FileHandler(os.path.join(log_folder_path, SUMMARY_LOG))
    summary_file_log.setLevel(logging.DEBUG)

    # create console handler that also logs everything
    # (this will be in the default tmux pane, the other panes will have
    #  tail -f running on the pool-specific log files)
    summary_console_log = logging.StreamHandler()
    summary_console_log.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    summary_file_log.setFormatter(formatter)
    summary_console_log.setFormatter(formatter)

    # add the handlers to the logger summary logger
    logger.addHandler(summary_file_log)
    logger.addHandler(summary_console_log)

    # next we create the pool specific loggers and add a file handler for each of them
    source_logger = logging.getLogger('repo.source')
    process_logger = logging.getLogger('repo.process')
    package_logger = logging.getLogger('repo.package')
    publish_logger = logging.getLogger('repo.publish')

    source_file_log = logging.FileHandler(os.path.join(log_folder_path, SOURCE_LOG))
    process_file_log = logging.FileHandler(os.path.join(log_folder_path, PROCESSING_LOG))
    package_file_log = logging.FileHandler(os.path.join(log_folder_path, PACKAGING_LOG))
    publish_file_log = logging.FileHandler(os.path.join(log_folder_path, PUBLISHING_LOG))

    source_file_log.setLevel(logging.DEBUG)
    process_file_log.setLevel(logging.DEBUG)
    package_file_log.setLevel(logging.DEBUG)
    publish_file_log.setLevel(logging.DEBUG)

    source_file_log.setFormatter(formatter)
    process_file_log.setFormatter(formatter)
    package_file_log.setFormatter(formatter)
    publish_file_log.setFormatter(formatter)

    source_logger.addHandler(source_file_log)
    process_logger.addHandler(process_file_log)
    package_logger.addHandler(package_file_log)
    publish_logger.addHandler(publish_file_log)

    logger.info("logging initialized")

