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

import time


class Package(object):
    # states

    LOADING = 1
    PROCESSING = 2
    DONE = 3

    def __init__(self):
        self._name = None
        self._size = None
        # this timestamp relates to when
        # the source data were last updated
        self.source_timestamp = None
        # repository path suffix
        # ex.: europe/france/ for French regions
        self._repo_sub_path = ""
        # current state of package processing
        self._state = None
        # combined time spend on package processing in seconds
        self._processing_time = 0
        # current loading progress 0.0 = 0%, 1.0 = 100%
        self._loading_progress = 0.0
        # a path to the source data file
        self._source_file_path = None
        # a temporary working directory for this package only
        self._temp_path = None

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return  self._size

    @property
    def state(self):
        return self._state

    @property
    def loading_progress(self):
        return self._loading_progress

    def _addProcessingTime(self, pTime):
        self._processing_time += pTime

    @property
    def processing_time(self):
        """return how long this package took to process so far in seconds"""
        return self._processing_time

    @property
    def source_file_path(self):
        return self._source_file_path

    @property
    def temp_path(self):
        return self._temp_path

    def _timeit(self, fn):
        def wrapped():
            start = time.time()
            fn()
            self._addProcessingTime(time.time() - start)

        return wrapped

    def load(self):
        """load any source data needed by the package to storage"""
        pass

    def process(self):
        """process the source data"""
        pass

    def package(self):
        """package the results"""
        pass

    def publish(self, path):
        """publish the data to the online repository"""
        pass

    def get_results(self):
        """return a list file-paths pointing to results
        of the processing & packaging steps that now need to be published
        """
        pass

    def clear_all(self):
        """clear all data created during package processing
        -> this currently means source & temporary data,
        not results, if they were already published"""


