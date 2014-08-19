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
import urllib
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
        self.preprocessorPath = manager.getMonavPreprocessorPath()
        self.manager = manager

    def getName(self):
        return "Monav"

    def getFolderName(self):
        return "monav"

    def _preUpdate(self):
        """make sure temporary & publishing folders exist"""
        if utils.createFolderPath(self.getTempPath()) == False:
            return False
        if utils.createFolderPath(self.getPublishPath()) == False:
            return False
        return True

    def _loadData(self, sourceQueue):
        # check from where to load data
        if self.manager.args.data_source == repo.DATA_SOURCE_FOLDER:
            sourceFolder = self.manager.args.source_data_folder
            self._loadLocalData(sourceQueue, sourceFolder)
        else:  # download data
            self._downloadData(sourceQueue)

    def _loadLocalData(self, sourceQueue, sourceFolder):
        source_log.info('local source data loader starting')
        tempPath = self.getTempPath()
        # store all PBF files to a list, so we
        # can print some stats on them & process them
        files = []
        accumulatedSize = 0
        source_log.info("loading data from local folder:")
        source_log.info("%s", os.path.abspath(sourceFolder))
        for root, dirs, dirFiles in os.walk(sourceFolder):
            for f in dirFiles:
                if os.path.splitext(f)[1] == ".pbf":
                    filePath = os.path.join(root, f)
                    fileSize = os.path.getsize(filePath)
                    accumulatedSize += fileSize
                    files.append( (filePath, fileSize) )
        fileCount = len(files)

        source_log.info("found %d PBF files together %s in size",
            fileCount, utils.bytes2PrettyUnitString(accumulatedSize)
        )

        # generate a package for every PBF file
        packId = 0
        for f, fSize in files:
            try:
                metadata = {
                    'packId': packId,
                    'tempPath': tempPath,
                    'helperPath': self.getFolderName(),
                    'preprocessorPath': self.preprocessorPath,
                    'filePath' : f,
                    'filePathPrefix' : sourceFolder
                }
                pack = MonavPackage(metadata)
                packId += 1
                sizeString = utils.bytes2PrettyUnitString(fSize)
                source_log.info('loading %d/%d: %s (%s)', packId, fileCount, pack.getName(), sizeString)
                pack.load()
                sourceQueue.put(pack)
            except Exception, e:
                source_log.exception('loading PBF file failed: %s', f)
                #source_log.error(e)
                #traceback.print_exc(file=sys.stdout)
                #source_log.exception("traceback:")

        source_log.info('all source files loaded')

    def _downloadData(self, sourceQueue):
        tempPath = self.getTempPath()
        csvFilePath = self.manager.getMonavCSVPath()
        # get a CSV line count to get approximate repository update progress
        urlCount = utils.countCSVLines(csvFilePath)
        if not urlCount: # just to be sure
            urlCount = 0
        f = open(csvFilePath, "r")
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
            sortedUrls = map(lambda x: (0, x), urls)
        else:
            # sort the URLs by size
            source_log.info('sorting URLs by size in ascending order')
            sortedUrls, totalSize = utils.sortUrlsBySize(urls)
            source_log.info('total download size: %s', utils.bytes2PrettyUnitString(totalSize))

        # download all the URLs
        packId = 0
        for size, url in sortedUrls:
            try:
                metadata = {
                    'packId': packId,
                    'tempPath': tempPath,
                    'helperPath': self.getFolderName(),
                    'preprocessorPath': self.preprocessorPath,
                    'url' : url,
                    'urlType': self._getSourceUrlType()
                }
                pack = MonavPackage(metadata)
                packId += 1
                if size is None:
                    sizeString = "unknown size"
                else:
                    sizeString = utils.bytes2PrettyUnitString(size)
                source_log.info('downloading %d/%d: %s (%s)', packId, urlCount, pack.getName(), sizeString)
                pack.load()
                sourceQueue.put(pack)
            except Exception, e:
                source_log.exception('loading url failed: %s', url)
                #source_log.info(e)
                #traceback.print_exc(file=sys.stdout)
                #source_log.exception("traceback:")

        source_log.info('all downloads finished')

    def _processPackage(self, sourceQueue, packQueue):
        """process OSM data in the PBF format into Monav routing data"""
        while True:
            package = sourceQueue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                sourceQueue.task_done()
                break
                # process the data

            # rough Monav-preprocessor thread count heuristics
            # * the packages will probably spend the most time
            # importing data, but many threads can speed up part of
            # the computation quite a bit
            # * with the default queue size (10), this means worst-case
            # over-commit of about 2.5 for Monav threads (+ max 10 active packaging threads)
            monavThreads = self.manager.getMonavPreprocessorThreads()
            # how many preprocessors can be run at once
            maxParallelPreprocessors = self.manager.getMonavParallelThreads()
            # source file size threshold (in MB) for running the preprocessors in parallel
            parallelThreshold = self.manager.getMonavParallelThreshold()
            # start packaging
            package.process((monavThreads, maxParallelPreprocessors), parallelThreshold)
            # signal task done
            sourceQueue.task_done()
            # forward the package to the packaging pool
            packQueue.put(package)
        process_log.info('processing shutting down')

    def _packagePackage(self, packQueue, publishQueue):
        """create a compressed TAR archive from the Monav routing data
        -> three packages (car, pedestrian, bike) are generated and compressed
        sequentially to three separate archives"""
        while True:
            package = packQueue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                packQueue.task_done()
                break
                # packaging
            package.package()
            # signal task done
            packQueue.task_done()
            # forward the package to the publishing process
            publishQueue.put(package)
        package_log.info('packaging shutting down')

    def _publishPackage(self, publishQueue):
        """tak the compressed TARs and publish them to the modRana public folder
        and update the repository manifest accordingly"""
        publish_log.info('publisher starting')
        while True:
            package = publishQueue.get()
            if package == repo.SHUTDOWN_SIGNAL:
                publishQueue.task_done()
                break
            publish_log.info('publishing %s' % package.getName())
            package.publish(self.getPublishPath())
            publishQueue.task_done()
        publish_log.info('publisher shutting down')

class MonavPackage(Package):
    def __init__(self, metadata):
        Package.__init__(self)
        self.url = metadata.get('url')
        urlType = metadata.get('urlType')
        self.filePath = metadata.get('filePath')
        self.filePathPrefix = metadata.get('filePathPrefix')
        self.helperPath = metadata.get('helperPath') # for accessing the base.ini file for Monav preprocessor
        self.preprocessorPath = metadata['preprocessorPath']
        # split to repoSubPath & filename
        # -> repoSubPath = continent/country/etc.
        if self.filePath:
            self.repoSubPath, self.filename, self.name = utils.pbfPath2repoPathFilenameName(
                self.filePath, self.filePathPrefix
            )
            self.sourceDataPath = self.filePath
        else: # url
            self.repoSubPath, self.filename, self.name = utils.url2repoPathFilenameName(self.url, urlType)
            self.sourceDataPath = os.path.join(self.tempStoragePath, self.filename)
        # a temporary working directory for this package only (unique id prefix)
        self.tempPath = os.path.join(metadata['tempPath'], str(metadata['packId']))
        # a subdirectory named after the package
        self.tempStoragePath = os.path.join(self.tempPath, self.name)

        # paths to resulting data files
        self.results = []

    def load(self):
        if self.filePath:
            self._loadFromFile()
        else:  # url
            self._download()

    def _loadFromFile(self):
        """Use local PBF file as data source"""
        try:
            if os.path.exists(self.sourceDataPath):
                if os.path.exists(self.tempStoragePath):
                    source_log.info('removing old temporary folder %s', self.tempStoragePath)
                    shutil.rmtree(self.tempStoragePath)
                utils.createFolderPath(self.tempStoragePath)
                return True
        except Exception, e:
            message = 'monav package: OSM PBF loading failed\n'
            message += 'name: %s\n' % self.name
            message += 'filePath: %s\n' % self.filePath
            message += 'storage path: %s' % self.sourceDataPath
            source_log.exception(message)
            #traceback.print_exc(file=sys.stdout)
            return False

    def _download(self):
        """download PBF extract from the URL and store it locally"""
        try:
            if os.path.exists(self.sourceDataPath):
                return
                # TODO: DEBUG, remove this
            else:
                if os.path.exists(self.tempStoragePath):
                    source_log.info('removing old folder %s' % self.tempStoragePath)
                    shutil.rmtree(self.tempStoragePath)
                utils.createFolderPath(self.tempStoragePath)
                #        f = open(self.sourceDataPath, "w")
                #        request = urllib2.urlopen(self.url)
                urllib.urlretrieve(self.url, self.sourceDataPath)
                #        f.write(request.read())
                #        f.close()
                return True
        except Exception, e:
            message = 'monav package: OSM PBF download failed\n'
            message += 'name: %s\n' % self.name
            message += 'URL: %s\n' % self.url
            message += 'storage path: %s' % self.sourceDataPath
            source_log.exception(message)
            # print(e)
            # traceback.print_exc(file=sys.stdout)
            return False

    def process(self, threads=(1, 1), parallelThreshold=None):
        """process the PBF extract into Monav routing data"""
        monavThreads, maxParallelPreprocessors = threads
        # check the parallel threshold
        if parallelThreshold is not None:
            try:
                fileSize = os.path.getsize(self.sourceDataPath)
            except OSError:
                fileSize = 0
                # check if file size in MB is larger than threshold
            if (fileSize / (2 ** 20)) > parallelThreshold:
                # if threshold is crossed, don't run preprocessors in parallel
                maxParallelPreprocessors = 1
        try:
            if parallelThreshold is None and maxParallelPreprocessors == 1:
                process_log.info('processing %s', self.getName())
            elif maxParallelPreprocessors == 1:
                process_log.info('processing %s in 1 thread (threshold reached)', self.getName())
            else: # >1
                process_log.info('processing %s in %d threads', self.getName(), maxParallelPreprocessors)
            start_time = time.time()
            inputFile = self.sourceDataPath
            outputFolder = self.tempStoragePath
            baseINIPath = os.path.join(self.helperPath, "base.ini")
            preprocessorPath = self.preprocessorPath

            def getTask(modeName, modeProfile, index):
                """prepare task that runs the preprocessor in temPath separate for every preprocessor instance and move
                the result to resultPath
                NOTE: the temporary folder is used to avoid multiple preprocessors mixing their temporary data"""
                tempOutputFolder = os.path.join(outputFolder, str(index))
                resultPath = os.path.join(tempOutputFolder, "routing_%s" % modeName)
                # compile arguments
                args = ['%s' % preprocessorPath, '-di', '-dro="%s"' % modeName, '-t=%d' % monavThreads, '--verbose',
                        '--settings="%s"' % baseINIPath,
                        '--input="%s"' % inputFile, '--output="%s"' % tempOutputFolder, '--name="%s"' % self.name,
                        '--profile="%s"' % modeProfile, '-dd']

                return args, resultPath, self.tempStoragePath

            def runPreprocessor(queue):
                """this function is run in an internal pool inside the Monav package"""

                while True:
                    task = queue.get()
                    if task == repo.SHUTDOWN_SIGNAL:
                        queue.task_done()
                        return
                    args, fromPath, toPath = task
                    # create the independent per-preprocessor path
                    os.makedirs(fromPath)

                    # open /dev/null so that the stdout & stderr output for the command can be dumped into it
                    fNull = open(os.devnull, "w")
                    # call the preprocessor
                    subprocess.call(reduce(lambda x, y: x + " " + y, args), shell=True, stdout=fNull, stderr=fNull)
                    # move the results to the main folder
                    shutil.move(fromPath, toPath)
                    # cleanup
                    fNull.close()
                    queue.task_done()

            tasks = [
                getTask("car", "motorcar", 0),
                getTask("bike", "bicycle", 1),
                getTask("pedestrian", "foot", 2)
            ]

            preprocQueue = mp.JoinableQueue()
            for i in range(maxParallelPreprocessors):
                p = mp.Process(target=runPreprocessor, args=(preprocQueue,))
                p.daemon = True
                p.start()
            for task in tasks:
                preprocQueue.put(task)
                # wait for the processes to finish
            preprocQueue.join()
            # shutdown them down
            for i in range(maxParallelPreprocessors):
                preprocQueue.put(repo.SHUTDOWN_SIGNAL)
            preprocQueue.join()
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
            process_log.info('processed %s in %s', self.getName(), utils.prettyTimeDiff(td))
            return True
        except Exception, e:
            message = 'monav package: Monav routing data processing failed\n'
            message += 'name: %s' % self.name
            process_log.exception(message)
            #print(e)
            #traceback.print_exc(file=sys.stdout)
            return False

    def package(self):
        """compress the Monav routing data"""
        modes = ["car", "bike", "pedestrian"]
        package_log.info('packaging %s', self.getName())
        for mode in modes:
            path = os.path.join(self.tempStoragePath, "routing_%s" % mode)
            archivePath = os.path.join(self.tempStoragePath, "%s_%s.tar.gz" % (self.name, mode))
            try:
                # fakeRoot -> we need to have this structure inside the archive:
                # /country/routing_x/
                # as the files are stored in temp/monav/number/country/routing_x
                # we supply a prefix, that is subtracted from the path using os.path.relpath()
                # Example:
                # temp/monav/0/azores/routing_car - temp/monav/0 = /azores/routing_car
                utils.tarDir(path, archivePath, fakeRoot=self.tempPath)
                #TODO: MD5 hash for archives
                self.results.append(archivePath)
            except Exception, e:
                message = 'monav package: compression failed\n'
                message += 'path: %s' % path
                message += 'archive: %s' % archivePath
                package_log.exception(message)
                #print(e)
                #traceback.print_exc(file=sys.stdout)
        if self.results:
            return True
        else:
            return False

    def publish(self, mainRepoPath, cleanup=True):
        """publish the package to the online repository"""

        for path2file in self.results:
            finalRepoPath = os.path.join(mainRepoPath, self.repoSubPath)
            try:
                # try to make sure the folder exists
                utils.createFolderPath(finalRepoPath)
                # move the results
                shutil.move(path2file, finalRepoPath)
            except Exception, e:
                message = 'monav package: publishing failed\n'
                message += 'file: %s' % path2file
                message += 'target path: %s' % finalRepoPath
                publish_log.exception(message)
                #print(e)
        if cleanup: # clean up any source & temporary files
            self.clearAll()

    def clearAll(self):
        """remove the whole temporary directory for this pack"""
        shutil.rmtree(self.tempPath)

