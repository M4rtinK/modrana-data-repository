#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository startup handling
# * parse startup arguments
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
import sys

from core.repo import QUEUE_SIZE

import core.argparse as argparse


class Startup:
    def __init__(self):
        parser = argparse.ArgumentParser(description="A flexible GPS navigation system.")
        # Config
        parser.add_argument(
            '-c', metavar="configuration file", type=str,
            help="load the configuration file from this path DEFAULT: repository.conf",
            default=None, action="store"
        )

        # Folders

        parser.add_argument(
            '--temp-folder', metavar="temporary folder", type=str,
            help='path to the temporary data folder',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--repository-folder', metavar='repository folder', type=str,
            help='path to the repository folder',
            default=None,
            action="store"
        )

        # multiprocessing variables

        parser.add_argument(
            '--cpu-count', metavar='cpu count', type=int,
            help='override logical CPU count',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--queue-size', metavar='package count', type=int,
            help='override default queue size DEFAULT: %d' % QUEUE_SIZE,
            default=None,
            action="store"
        )
        parser.add_argument(
            '--source-queue-size', metavar='package count', type=int,
            help='set the source data queue size DEFAULT: %d' % QUEUE_SIZE,
            default=None,
            action="store"
        )
        parser.add_argument(
            '--processing-pool-size', metavar='process count', type=int,
            help='size of the processing pool DEFAULT: cpu count',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--packaging-queue-size', metavar='package count', type=int,
            help='packaging queue size DEFAULT: %d' % QUEUE_SIZE,
            default=None,
            action="store"
        )
        parser.add_argument(
            '--packaging-pool-size', metavar='process count', type=int,
            help='size of the packaging pool DEFAULT: cpu count',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--publish-queue-size', metavar='package count', type=int,
            help='publishing queue size DEFAULT: %d' % QUEUE_SIZE,
            default=None,
            action="store"
        )

        # Monav repository variables

        parser.add_argument(
            '--monav-preprocessor-threads', metavar='thread count', type=int,
            help='thread count for the Monav preprocessor DEFAULT: max(1,cpu_count/4)',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--monav-preprocessor-path', metavar='monav-preprocessor binary', type=str,
            help='path to the Monav preprocessor binary',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--monav-pool-size', metavar='process count', type=int,
            help='how many monav-preprocessors should be run in parallel per package DEFAULT: 1 MAX: 3 NOTE: this can triple memory usage',
            default=None,
            action="store"
        )
        parser.add_argument(
            '--monav-pool-threshold', metavar='source file size in megabytes', type=int,
            help="if the source data file for a package is larger than this, don't run monav-preprocessors in parallel DEFAULT: not set",
            default=None,
            action="store"
        )
        parser.add_argument(
            '--monav-csv-path', metavar='CSV file', type=str,
            help="CSV file with links to PBF extracts, used as a basis for Monav routing data packages DEFAULT: monav/osm_pbf_extracts.csv",
            default=None,
            action="store"
        )
        parser.add_argument(
            '--monav-dont-sort-urls',
            help="don't sort PBF URLs by size (sensible choice for very long lists or URLs)",
            default=False,
            action="store_true"
        )

        self.args = parser.parse_args()

    def getArgs(self):
        """return parsed CLI arguments"""
        return self.args

    def _exit(self, errorCode=0):
        sys.exit(errorCode)

