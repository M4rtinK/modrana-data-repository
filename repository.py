#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository - core
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

import multiprocessing as mp
import time
import logging
log = logging.getLogger("repo")

from monav import MonavRepository, PREPROCESSOR_PATH, SOURCE_DATA_URLS_CSV
from core.configobj.configobj import ConfigObj
from core import repo
from core import utils
from core import startup
from core import repo_log

# keywords
SHUTDOWN_KEYWORD = "shutdown"
# folders
TEMP_PATH = "temp"
RESULTS_PATH = "results"
CONFIG_FILE_PATH = "repository.conf"

# decorators
def integer(fn):
    def wrapper(self):
        return int(fn(self))

    return wrapper


def string(fn):
    def wrapper(self):
        return str(fn(self))

    return wrapper


class Manager(object):
    """manages the overall repository state, including updating all
    sub-repositories"""

    def __init__(self):
        # load the configuration file
        self._args = startup.Startup().getArgs()
        self._conf = ConfigObj(self.config_path)

        # initialize logging
        repo_log.init_logging(self.log_folder_path)

        # for now, update all repositories
        self.updateAll()

    def updateAll(self):
        log.info("## starting repository update ##")
        start = time.time()
        #log.info("%d,%d,%d", self.cpu_count,  self.processing_pool_size, self.packaging_pool_size)
        log.info("# CPU count: %d, proc. pool: %d, pack pool: %d",
        self.cpu_count,
        self.processing_pool_size,
        self.packaging_pool_size)
        log.info("# queues: source: %d, pack: %d, publish: %d",
        self.source_queue_size,
        self.packaging_queue_size,
        self.publish_queue_size)
        log.info("## updating Monav repository" )
        log.info('# monav preprocessor threads: %d', self.monav_preprocessor_threads)
        log.info('# max parallel pp. per package: %d', self.monav_parallel_threads)
        ppThreshold = self.monav_parallel_threshold
        if ppThreshold:
            log.info('# parallel pp. threshold: %d MB' % ppThreshold)
        start_monav = time.time()
        monav = MonavRepository(self)
        monav.update()
        # log how long the Monav update took
        dt_monav = int(time.time() - start_monav)
        if dt_monav > 60:
            prettyTime = "%s (%d s)" % (utils.prettyTimeDiff(dt_monav), dt_monav)
            # show seconds for exact benchmarking once pretty time
            # switches to larger units
        else:
            prettyTime = utils.prettyTimeDiff(dt_monav)
        log.info("## Monav repository updated in %s " % prettyTime)

        log.info("## Summary:")
        log.info("## Monav repository updated in %s (%d s)" %
                 (utils.prettyTimeDiff(dt_monav), dt_monav)
        )

        # log how long the repository update took
        dt = int(time.time() - start)
        if dt > 60:
            prettyTime = "%s (%d s)" % (utils.prettyTimeDiff(dt), dt)
        else:
            prettyTime = utils.prettyTimeDiff(dt)
        log.info("## Repository updated in %s " % prettyTime)

        log.info("## repository update finished ##")

    @property
    def config(self):
        """return parsed config file"""
        return self._conf

    @property
    def args(self):
        """return the CLI options dictionary"""
        return self._args

    # Configuration variable wrappers
    @property
    def config_path(self):
        """get configuration file path"""
        if self.args.c is not None:
            return self.args.c
        else:
            return repo.CONFIG_FILE_PATH

    @property
    def temp_path(self):
        """temporary folder path wrapper"""
        return self._wrapVariable(self.args.temp_folder, "temporary_folder", repo.TEMP_PATH)

    @property
    def repo_path(self):
        """repository folder path wrapper"""
        return self._wrapVariable(self.args.repository_folder, "repository_folder", repo.RESULTS_PATH)

    @property
    def data_source_type(self):
        """data source type wrapper"""
        return self._wrapVariable(self.args.data_source, "data_source", repo.DEFAULT_DATA_SOURCE)

    @property
    def source_data_path(self):
        """source data path wrapper"""
        return self._wrapVariable(self.args.source_data_folder, "source_data_folder", repo.DEFAULT_SOURCE_FOLDER)

    @property
    def log_folder_path(self):
        """source data path wrapper"""
        return self._wrapVariable(self.args.log_folder, "log_folder", "logs/repo_update_logs_%s" % time.strftime("%Y.%m.%d-%H:%M:%S"))

    @property
    @integer
    def cpu_count(self):
        """cpu count wrapper"""
        return self._wrapVariable(self.args.cpu_count, "cpu_count", mp.cpu_count())

    @property
    @integer
    def source_queue_size(self):
        """source queue size wrapper"""
        return self._wrapVariable(self.args.source_queue_size, "source_queue_size", repo.QUEUE_SIZE)

    @property
    @integer
    def packaging_queue_size(self):
        """packaging queue size wrapper"""
        return self._wrapVariable(self.args.packaging_queue_size, "packaging_queue_size", repo.QUEUE_SIZE)

    @property
    @integer
    def publish_queue_size(self):
        """publishing queue size wrapper"""
        return self._wrapVariable(self.args.publish_queue_size, "publish_queue_size", repo.QUEUE_SIZE)

    @property
    @integer
    def processing_pool_size(self):
        """processing pool size wrapper"""
        return self._wrapVariable(self.args.processing_pool_size, "processing_pool_size", mp.cpu_count())

    @property
    @integer
    def packaging_pool_size(self):
        """packaging pool size wrapper"""
        return self._wrapVariable(self.args.packaging_pool_size, "packaging_pool_size", mp.cpu_count())

    # Monav variable wrappers

    @property
    @string
    def monav_preprocessor_path(self):
        """Monav preprocessor path wrapper"""
        return self._wrapVariable(self.args.monav_preprocessor_path, "monav_preprocessor_path", PREPROCESSOR_PATH)

    @property
    @integer
    def monav_preprocessor_threads(self):
        """Monav preprocessor thread count wrapper"""
        cpu_count = int(self.cpu_count)
        return self._wrapVariable(self.args.monav_preprocessor_threads, "monav_preprocessor_threads",
                                  max(1, cpu_count / 4))

    @property
    @integer
    def monav_parallel_threads(self):
        """Monav preprocessor parallel thread count wrapper
        -> how many preprocessors would be run in parallel"""
        return self._wrapVariable(self.args.monav_pool_size, "monav_parallel_threads", 1)

    @property
    def monav_parallel_threshold(self):
        """Monav preprocessor parallel run threshold wrapper
        -> don't run monav preprocessors in parallel is source data is larger than threshold"""
        result = self._wrapVariable(self.args.monav_pool_threshold, "monav_parallel_threshold", None)
        if result is not None:
            return int(result)
        else:
            return result

    @property
    @string
    def monav_csv_path(self):
        """path to a CSV file with links to PBF extracts for Monav wrapper"""
        return self._wrapVariable(self.args.monav_csv_path, "monav_csv_path", SOURCE_DATA_URLS_CSV)

    def _wrapVariable(self, option, confKey, default):
        if option is not None:
            return option
        else:
            return self.config.get(confKey, default)


if __name__ == '__main__':
    Manager()


