#! /usr/bin/python3
import click
import os
import subprocess
import urllib.request

class LLVMResourceHandler:
    @staticmethod
    def createHandler(versionString,archiveDir,srcDir):
        if versionString == 'trunk':
            return LLVMTrunkHandler(versionString, archiveDir, srcDir)
        else:
            return LLVMArchiveHandler(versionString, archiveDir, srcDir)

    @staticmethod
    def getComponentSpecs(component):
        if component == 'cfe':
            return 'clang', 'tools'
        elif component == 'compiler-rt':
            return 'compiler-rt', 'projects'
        elif component == 'libunwind':
            return 'libunwind', 'projects'
        elif component == 'openmp':
            return 'openmp', 'projects'
        elif component == 'libcxx':
            return 'libcxx', 'projects'
        elif component == 'libcxxabi':
            return 'libcxxabi', 'projects'
        elif component == 'clang-tools-extra':
            return 'extra', 'tools'
        elif component == 'lldb':
            return 'lldb', 'tools'
        elif component == 'test-suite':
            return 'test-suite', 'projects'
        else:
            raise RuntimeError('Unknown component: {0}'.format(component))

class LLVMTrunkHandler(LLVMResourceHandler):
    def __init__(self, version, archiveDir, srcDir):
        self['version'] = version
        self['archive'] = archiveDir
        self['src'] = srcDir

    def setupLLVMCore(self):
        pass

    def setupComponent(self,component):
        pass

class LLVMArchiveHandler(LLVMResourceHandler):
    def __init__(self, version, archiveDir, srcDir):
        self.version = version
        self.archiveDir = archiveDir
        self.srcDir = srcDir
        self.baseURL = 'http://llvm.org/releases/{0}/'
        self.baseFileName = '{0}-{1}.src.tar.xz'

    def setupLLVMCore(self):
        llvmArchive = self.downloadArchive('llvm', self.archiveDir)
        self.extractArchive(llvmArchive, self.srcDir, None, 1)

    def setupComponent(self,component):
        compArchive = self.downloadArchive(component, self.archiveDir)
        localName, localDir = LLVMResourceHandler.getComponentSpecs(component)
        self.extractArchive(compArchive, os.path.join(self.srcDir, localDir), localName)

    def downloadArchive(self,component,archiveDir):
        fileName = self.baseFileName.format(component, self.version) 
        componentURL = self.baseURL.format(self.version) + fileName
        archiveFileName = os.path.join(archiveDir, fileName)
        urllib.request.urlretrieve(componentURL, archiveFileName)
        return archiveFileName

    def extractArchive(self,archiveFile,srcDir,localDirName=None,strip = False):
        if strip:
            stripSize = 1
        else:
            stripSize = 0
        if localDirName is None:
            srcDirName = srcDir
        else:
            srcDirName = os.path.join(srcDir, localDirName)
            os.makedirs(srcDirName)
            stripSize = 1
        command = 'tar xf {0} -C {1} --strip {2}'.format(archiveFile, srcDirName, str(stripSize))
        subprocess.call(command.split(), shell=False)

@click.command()
@click.option('--llvm-version', '-v', type=click.STRING, multiple=True, help='The LLVM version (or keyword trunk) to setup')
@click.argument('target-directory', type=click.Path(True,False,True,True,True,True))
@click.argument('llvm-components', nargs=-1, type=click.Choice(['cfe', 'compiler-rt', 'libcxx', 'libcxxabi', 'libunwind', 'openmp', 'clang-tools-extra', 'lldb', 'test-suite']))
def main (**kwargs):
    rootDir = kwargs['target_directory']
    llvmVersions = kwargs['llvm_version']
    llvmComponents = kwargs['llvm_components']
    if len(llvmComponents) == 0:
        # download all
        llvmComponents = ['cfe', 'compiler-rt', 'libcxx', 'libcxxabi', 'libunwind', 'openmp', 'clang-tools-extra', 'lldb', 'test-suite']
    # setup LLVM
    for v in llvmVersions:
        targetDir = getTargetDirectory(rootDir, v)
        dirs = setupTargetDirectory(targetDir)
        resourceHandler = LLVMResourceHandler.createHandler(v, dirs['archive'], dirs['src'])
        resourceHandler.setupLLVMCore()
        for c in llvmComponents:
            resourceHandler.setupComponent(c)

def getTargetDirectory(dir,version):
    return os.path.join(dir,version)

def setupTargetDirectory(dir):
    #if os.path.exists(dir):
    #    raise RuntimeError('The target directory {0} already exists'.format(dir))
    targetDirs = { compDir : os.path.join(dir,compDir) for compDir in ['archive', 'build', 'install', 'src'] }
    for key,value in targetDirs.items():
        os.makedirs(value)
    return targetDirs

if __name__ == '__main__':
    #try:
    main()
    #except Exception as e:
    #    print('Failed to setup LLVM: {0}'.format(e))
