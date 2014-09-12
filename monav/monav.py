# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Monav data repository
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
import shutil
import subprocess
import csv
import os
import multiprocessing as mp
import logging
import time
log = logging.getLogger("repo")
source_log = logging.getLogger('repo.source.monav')
process_log = logging.getLogger('repo.process.monav')
package_log = logging.getLogger('repo.package.monav')
publish_log = logging.getLogger('repo.publish.monav')

from core.package import Package
from core.repo import Repository
import core.repo as repo
import core.utils as utils

SOURCE_DATA_URLS_CSV = "monav/osm_pbf_extracts.csv"

PREPROCESSOR_PATH = "monav-preprocessor"


class MonavRepository(Repository):
    def __init__(self, manager):
        Repository.__init__(self, manager)
        self._preprocessor_path = manager.monav_preprocessor_path

    @property
    def name(self):
        return "Monav"

    @property
    def folder_name(self):
        return "monav"

    def _pre_update(self):
        """make sure temporary & publishing folders exist"""
        if utils.createFolderPath(self.temp_path) == False:
            return False
        if utils.createFolderPath(self.publish_path) == False:
            return False
        return True

    def _load_data(self):
        # check from where to load data
        if self.manager.args.data_source == repo.DATA_SOURCE_FOLDER:
            source_folder = self.manager.args.source_data_folder
            self._load_local_source_data(source_folder)
        else:  # download data
            self._download_source_data()

    def _load_local_source_data(self, source_folder):
        source_log.info('local source data loader starting')
        # store all PBF files to a list, so we
        # can print some stats on them & process them
        files = []
        accumulated_size = 0
        source_log.info("loading data from local folder:")
        source_log.info("%s", os.path.abspath(source_folder))
        for root, dirs, dirFiles in os.walk(source_folder):
            for f in dirFiles:
                if os.path.splitext(f)[1] == ".pbf":
                    file_path = os.path.join(root, f)
                    file_size = os.path.getsize(file_path)
                    accumulated_size += file_size
                    files.append( (file_path, file_size) )
        file_count = len(files)

        source_log.info("found %d PBF files together %s in size",
            file_count, utils.bytes2PrettyUnitString(accumulated_size)
        )
        return files

    def _generate_monav_packages(self, source_folder, file_size_list):
        # generate a package for every PBF file
        pack_id = 0
        for f, f_size in file_size_list:
            try:
                metadata = {
                    'packId': pack_id,
                    'tempPath': self.temp_path,
                    'helperPath': self.folder_name,
                    'preprocessorPath': self._preprocessor_path,
                    'filePath' : f,
                    'filePathPrefix' : source_folder
                }
                pack = MonavPackage(metadata)
                pack_id += 1
                size_string = utils.bytes2PrettyUnitString(f_size)
                file_count = len(file_size_list)
                source_log.info('loading %d/%d: %s (%s)', pack_id, file_count, pack.name(), size_string)
                pack.load()
                self.source_queue.put(pack)
            except Exception:
                source_log.exception('loading PBF file failed: %s', f)
                #source_log.error(e)
                #traceback.print_exc(file=sys.stdout)
                #source_log.exception("traceback:")

        source_log.info('all source files loaded')

    def _download_source_data(self):
        csv_file_path = self.manager.monav_csv_path
        # get a CSV line count to get approximate repository update progress
        urlCount = utils.countCSVLines(csv_file_path)
        if not urlCount: # just to be sure
            urlCount = 0
        f = open(csv_file_path, "r")
        reader = csv.reader(f)
        source_log.info('source data downloader starting')
        # read all URLs to a list
        urls = []
        for row in reader:
            if len(row) > 0:
                urls.append(row[0])
        f.close()

        if self.manager.args.monav_dont_sort_urls:
            source_log.info('URL sorting disabled')
            sorted_urls = map(lambda x: (0, x), urls)
        else:
            # sort the URLs by size
            source_log.info('sorting URLs by size in ascending order')
            sorted_urls, totalSize = utils.sortUrlsBySize(urls)
            source_log.info('total download size: %s', utils.bytes2PrettyUnitString(totalSize))

        # download all the URLs
        pack_id = 0
        for size, url in sorted_urls:
            try:
                metadata = {
                    'packId': pack_id,
                    'tempPath': self.temp_path,
                    'helperPath': self.folder_name,
                    'preprocessorPath': self._preprocessor_path,
                    'url' : url,
                    'urlType': self._get_source_url_type()
                }
                pack = MonavPackage(metadata)
                pack_id+= 1
                if size is None:
                    size_string = "unknown size"
                else:
                    size_string = utils.bytes2PrettyUnitString(size)
                source_log.info('downloading %d/%d: %s (%s)', pack_id, urlCount, pack.name(), size_string)
                pack.load()
                self.source_queue.put(pack)
            except Exception:
                source_log.exception('loading url failed: %s', url)
                #source_log.info(e)
                #traceback.print_exc(file=sys.stdout)
                #source_log.exception("traceback:")

        source_log.info('all downloads finished')

    def _process_package(self):
        """process OSM data in the PBF format into Monav routing data"""
        while True:
            package = self.source_queue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                self.source_queue.task_done()
                break
                # process the data

            # rough Monav-preprocessor thread count heuristics
            # * the packages will probably spend the most time
            # importing data, but many threads can speed up part of
            # the computation quite a bit
            # * with the default queue size (10), this means worst-case
            # over-commit of about 2.5 for Monav threads (+ max 10 active packaging threads)
            monavThreads = self.manager.monav_preprocessor_threads
            # how many preprocessors can be run at once
            maxParallelPreprocessors = self.manager.monav_parallel_threads
            # source file size threshold (in MB) for running the preprocessors in parallel
            parallelThreshold = self.manager.monav_parallel_threshold
            # start packaging
            package.process((monavThreads, maxParallelPreprocessors), parallelThreshold)
            # signal task done
            self.source_queue.task_done()
            # forward the package to the packaging pool
            self.packaging_queue.put(package)
        process_log.info('processing shutting down')

    def _package_package(self):
        """create a compressed TAR archive from the Monav routing data
        -> three packages (car, pedestrian, bike) are generated and compressed
        sequentially to three separate archives"""
        while True:
            package = self.packaging_queue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                self.packaging_queue.task_done()
                break
                # packaging
            package.package()
            # signal task done
            self.packaging_queue.task_done()
            # forward the package to the publishing process
            self.publish_queue.put(package)
        package_log.info('packaging shutting down')

    def _publish_package(self):
        """tak the compressed TARs and publish them to the modRana public folder
        and update the repository manifest accordingly"""
        publish_log.info('publisher starting')
        while True:
            package = self.publish_queue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                self.publish_queue.task_done()
                break
            publish_log.info('publishing %s', package.name)
            package.publish(self.publish_path)
            self.publish_queue.task_done()
        publish_log.info('publisher shutting down')

class MonavPackage(Package):
    def __init__(self, metadata):
        Package.__init__(self, metadata)
        self._helper_path = metadata.get('helperPath') # for accessing the base.ini file for Monav preprocessor
        self._preprocessor_path = metadata['preprocessorPath']

        # paths to resulting data files
        self.results = []

    def process(self, threads=(1, 1), parallel_threshold=None):
        """process the PBF extract into Monav routing data"""
        monav_threads, max_parallel_preprocessors = threads
        # check the parallel threshold
        if parallel_threshold is not None:
            try:
                file_size = os.path.getsize(self._source_data_path)
            except OSError:
                file_size = 0
                # check if file size in MB is larger than threshold
            if (file_size / (2 ** 20)) > parallel_threshold:
                # if threshold is crossed, don't run preprocessors in parallel
                max_parallel_preprocessors = 1
        try:
            if parallel_threshold is None and max_parallel_preprocessors == 1:
                process_log.info('processing %s', self.name())
            elif max_parallel_preprocessors == 1:
                process_log.info('processing %s in 1 thread (threshold reached)', self.name())
            else: # >1
                process_log.info('processing %s in %d threads', self.name(), max_parallel_preprocessors)
            start_time = time.time()
            input_file = self._source_data_path
            output_folder = self._temp_storage_path
            base_INI_Path = os.path.join(self._helper_path, "base.ini")
            preprocessor_path = self._preprocessor_path

            def get_task(mode_name, mode_profile, index):
                """prepare task that runs the preprocessor in temPath separate for every preprocessor instance and move
                the result to resultPath
                NOTE: the temporary folder is used to avoid multiple preprocessors mixing their temporary data"""
                temp_output_folder = os.path.join(output_folder, str(index))
                result_path = os.path.join(temp_output_folder, "routing_%s" % mode_name)
                # compile arguments
                args = ['%s' % preprocessor_path, '-di', '-dro="%s"' % mode_name, '-t=%d' % monav_threads, '--verbose',
                        '--settings="%s"' % base_INI_Path,
                        '--input="%s"' % input_file, '--output="%s"' % temp_output_folder, '--name="%s"' % self.name,
                        '--profile="%s"' % mode_profile, '-dd']

                return args, result_path, self._temp_storage_path

            def run_preprocessor(queue):
                """this function is run in an internal pool inside the Monav package"""

                while True:
                    current_task = queue.get()
                    if current_task == repo.SHUTDOWN_SIGNAL:
                        queue.task_done()
                        return
                    args, from_path, to_path = current_task
                    # create the independent per-preprocessor path
                    os.makedirs(from_path)

                    # open /dev/null so that the stdout & stderr output for the command can be dumped into it
                    dev_null = open(os.devnull, "w")
                    # call the preprocessor
                    subprocess.call(reduce(lambda x, y: x + " " + y, args), shell=True, stdout=dev_null, stderr=dev_null)
                    # move the results to the main folder
                    shutil.move(from_path, to_path)
                    # cleanup
                    dev_null.close()
                    queue.task_done()

            tasks = [
                get_task("car", "motorcar", 0),
                get_task("bike", "bicycle", 1),
                get_task("pedestrian", "foot", 2)
            ]

            preproc_queue = mp.JoinableQueue()
            for i in range(max_parallel_preprocessors):
                p = mp.Process(target=run_preprocessor, args=(preproc_queue,))
                p.daemon = True
                p.start()
            for task in tasks:
                preproc_queue.put(task)
                # wait for the processes to finish
            preproc_queue.join()
            # shutdown them down
            for i in range(max_parallel_preprocessors):
                preproc_queue.put(repo.SHUTDOWN_SIGNAL)
            preproc_queue.join()
            # run preprocessors in parallel (depending on current settings)
            #      pool = mp.Pool(processes=maxParallelPreprocessors)
            #      pool.map(runPreprocessor, tasks)
            # closing the pool is important, otherwise the workers in the poll will
            # not exit - after a while the inactive threads will accumulate and
            # no more new ones can be started
            #      pool.close()
            # just to be sure
            #      pool.join()
            td = int(time.time() - start_time)
            process_log.info('processed %s in %s', self.name(), utils.prettyTimeDiff(td))
            return True
        except Exception:
            message = 'monav package: Monav routing data processing failed\n'
            message += 'name: %s' % self.name
            process_log.exception(message)
            return False

    def package(self):
        """compress the Monav routing data"""
        modes = ["car", "bike", "pedestrian"]
        package_log.info('packaging %s', self.name())
        for mode in modes:
            path = os.path.join(self._temp_storage_path, "routing_%s" % mode)
            archive_path = os.path.join(self._temp_storage_path, "%s_%s.tar.gz" % (self.name, mode))
            try:
                # fakeRoot -> we need to have this structure inside the archive:
                # /country/routing_x/
                # as the files are stored in temp/monav/number/country/routing_x
                # we supply a prefix, that is subtracted from the path using os.path.relpath()
                # Example:
                # temp/monav/0/azores/routing_car - temp/monav/0 = /azores/routing_car
                utils.tarDir(path, archive_path, fakeRoot=self._temp_path)
                #TODO: MD5 hash for archives
                self.results.append(archive_path)
            except Exception:
                message = 'monav package: compression failed\n'
                message += 'path: %s' % path
                message += 'archive: %s' % archive_path
                package_log.exception(message)
        if self.results:
            return True
        else:
            return False

    def publish(self, main_repo_path, cleanup=True):
        """publish the package to the online repository"""

        for path2file in self.results:
            finalRepoPath = os.path.join(main_repo_path, self._repo_sub_path)
            try:
                # try to make sure the folder exists
                utils.createFolderPath(finalRepoPath)
                # move the results
                shutil.move(path2file, finalRepoPath)
            except Exception:
                message = 'monav package: publishing failed\n'
                message += 'file: %s' % path2file
                message += 'target path: %s' % finalRepoPath
                publish_log.exception(message)
        if cleanup: # clean up any source & temporary files
            self.clear_all()

    def clear_all(self):
        """remove the whole temporary directory for this pack"""
        shutil.rmtree(self.temp_path)