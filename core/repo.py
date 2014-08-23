#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository - core
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free softwa
# re: you can redistribute it and/or modify
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

import multiprocessing as mp
import os
import logging
log = logging.getLogger("repo")

# pool & queue sizes
CPU_COUNT = mp.cpu_count()
QUEUE_SIZE = 10
SOURCE_DATA_QUEUE_SIZE = QUEUE_SIZE
PROCESSING_POOL_SIZE = CPU_COUNT
PACKAGING_QUEUE_SIZE = QUEUE_SIZE
PACKAGING_POOL_SIZE = CPU_COUNT
PUBLISHING_QUEUE_SIZE = QUEUE_SIZE
# keywords
SHUTDOWN_SIGNAL = "shutdown"
# folders
TEMP_PATH = "temp"
RESULTS_PATH = "results"
CONFIG_FILE_PATH = "repository.conf"
DEFAULT_SOURCE_FOLDER = "planet/split"
# URL types
GEOFABRIK_URL = 1
# data source types
DATA_SOURCE_FOLDER = "folder"
DATA_SOURCE_DOWNLOAD = "download"
DEFAULT_DATA_SOURCE = DATA_SOURCE_DOWNLOAD


class Repository(object):
    def __init__(self, manager):
        self._manager = manager

        # the source queue is fed by the data loader
        self._source_queue = mp.JoinableQueue(manager.source_queue_size)
        # the packaging queue is fed by the processing processes
        self._packaging_queue = mp.JoinableQueue(manager.packaging_queue_size)
        # the publishing queue is fed by the packaging processes
        self._publish_queue = mp.JoinableQueue(manager.publish_queue_size)

        # loads data for processing
        self._loading_process = None
        # publishes packages to online repository
        self._publishing_process = None

    @property
    def name(self):
        """return a pretty name for the repository"""
        raise NotImplementedError

    @property
    def folder_name(self):
        """return folder name for the repository"""
        raise NotImplementedError

    @property
    def source_queue(self):
        return self._source_queue

    @property
    def packaging_queue(self):
        return self._packaging_queue

    @property
    def publish_queue(self):
        return self._publish_queue

    @property
    def loading_process(self):
        return self._loading_process

    @property
    def publishing_process(self):
        return self._loading_process

    @property
    def manager(self):
        return self._manager

    def update(self):
        # run pre-update
        if self._pre_update() == False:
            log.error('repository pre-update failed')
            return False
            # start the loading process
        tempPath = self.temp_path
        self._loading_process = mp.Process(target=self._load_data)
        self._loading_process.daemon = True
        self._loading_process.start()
        # start the processing processes
        for i in range(self.processing_pool_size):
            p = mp.Process(target=self._process_package)
            p.daemon = False
            p.start()
            # start the packaging processes
        for i in range(self.packaging_pool_size):
            p = mp.Process(target=self._package_package)
            p.daemon = True
            p.start()
            # start the publishing process
        self._publishing_process = mp.Process(target=self._publish_package)
        self._publishing_process.daemon = True
        self._publishing_process.start()

        # start a method that first joins the first process, once it stops it joins
        # all the queues in sequence and feeds them with shutdown commands corresponding to the number of
        # worker processes corresponding to the given Queue
        # -> this shut shut-down the whole operation in sequence on the individual stages dry up
        self._terminate_once_done()

        # run post-update
        if self._post_update() == False:
            log.error('repository post-update failed')
            return False
        return True

    def _terminate_once_done(self):
        """terminate processes through their input queue
        once the previous stage runs out of work"""
        # first wait fo the loader to finish
        self.loading_process.join()

        # then shut down all the stages in sequence as they run out of work
        stages = [
            (self.source_queue, self.processing_pool_size),
            (self.packaging_queue, self.packaging_pool_size),
            (self.publish_queue, 1)
        ]

        for queue, processCount in stages:
            # join the queue and wait for any work units to be finished
            queue.join()
            # now send to shutdown commands to the processes feeding from the queue
            for i in range(processCount):
                queue.put(SHUTDOWN_SIGNAL)
                # wait for the shutdown signals to be processed
            queue.join()

    @property
    def processing_pool_size(self):
        """returns the number of threads to start in the data processing pool
        NOTE: this number should not change once the processing threads are started,
        as it might prevent a clean shutdown"""
        return self._manager.processing_pool_size

    @property
    def packaging_pool_size(self):
        """returns the number of threads to start in the data packaging pool
        NOTE: this number should not change once the packaging threads are started,
        as it might prevent a clean shutdown"""
        return self._manager.packaging_pool_size

    def _pre_update(self):
        """this method is called before starting the repository update"""
        pass

    def _post_update(self):
        """this method is called after finishing the repository update """
        pass

    ## Multiprocessing tasks ##
    def _load_data(self):
        pass

    def _process_package(self):
        pass

    def _package_package(self):
        pass

    def _publish_package(self):
        pass

    ## Paths ##
    @property
    def temp_path(self):
        return os.path.join(
            self._manager.temp_path,
            self.folder_name)

    @property
    def publish_path(self):
        return os.path.join(
            self._manager.repo_path,
            self.folder_name)

    ## Source data URLs ##
    def _get_source_url_type(self):
        # TODO: config file switch for setting this,
        # so that using the URL verbatim is possible
        return GEOFABRIK_URL
