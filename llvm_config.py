#! /usr/bin/python3
import click
import os
import subprocess
import urllib.request
from git import Repo

class LLVMResourceHandler:
    llvmResourceFile = '.llvm_config'
    @staticmethod
    def createHandler(versionString, rootDir, archiveDir, srcDir, repoType):
        if versionString == 'trunk':
            return LLVMTrunkHandler(versionString, rootDir, archiveDir, srcDir, repoType)
        else:
            return LLVMArchiveHandler(versionString, rootDir, archiveDir, srcDir)

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
            return 'extra', 'tools/clang/tools'
        elif component == 'lldb':
            return 'lldb', 'tools'
        elif component == 'test-suite':
            return 'test-suite', 'projects'
        else:
            raise RuntimeError('Unknown component: {0}'.format(component))

    @staticmethod
    def getComponentDepends(component):
        if component == 'clang-tools-extra':
            return ['cfe']
        else:
            return []

    @staticmethod
    def installComponent(component, srcDir):
        if not LLVMResourceHandler.isComponentInstalled(component, srcDir):
            file = open(os.path.join(srcDir, LLVMResourceHandler.llvmResourceFile), 'a')
            file.write('{0}\n'.format(component))


    @staticmethod
    def isComponentInstalled(component, srcDir):
        file = open(os.path.join(srcDir, LLVMResourceHandler.llvmResourceFile), 'r')
        for line in file:
            if line.strip().rstrip() == component:
                return True
        return False

    @staticmethod
    def setupLLVMResource(srcDir):
        open(os.path.join(srcDir, LLVMResourceHandler.llvmResourceFile), 'a').close()

    @staticmethod
    def isLLVMResource(srcDir):
        return os.path.exists(os.path.join(srcDir, LLVMResourceHandler.llvmResourceFile))

class LLVMTrunkHandler(LLVMResourceHandler):
    def __init__(self, version, rootDir, archiveDir, srcDir, repoType):
        self.version = version
        self.rootDir = rootDir
        self.archiveDir = archiveDir
        self.srcDir = srcDir
        self.repoType = repoType
        self.gitURL = 'http://llvm.org/git/{0}.git'
        self.svnURL = 'http://llvm.org/svn/llvm-project/{0}/trunk'
        self.svnCommand = ['svn', 'checkout', '--non-interactive']

    def getGITMapping (self, component):
        if component == 'cfe':
            return 'clang'
        else:
            return component

    def setupLLVMCore(self):
        if not LLVMResourceHandler.isComponentInstalled('llvm', self.rootDir):
            self.checkoutRepo('llvm', self.srcDir)
            LLVMResourceHandler.installComponent('llvm', self.rootDir)
        else:
            print('[{0}] LLVM core is already setup'.format(self.version))

    def setupComponent(self,component):
        if not LLVMResourceHandler.isComponentInstalled(component, self.rootDir):
            dependencies = LLVMResourceHandler.getComponentDepends(component)
            for c in dependencies:
                self.setupComponent(c)
            localName, localDir = LLVMResourceHandler.getComponentSpecs(component)
            self.checkoutRepo(component, os.path.join(self.srcDir, localDir, localName))
            LLVMResourceHandler.installComponent(component, self.rootDir)

    def checkoutRepo(self, component, targetDir):
        if self.repoType == 'svn':
            svnURL = self.svnURL.format(component)
            print('[{0}] SVN Checkout: {1} into {2}'.format(self.version, svnURL, targetDir))
            cmd = self.svnCommand + [self.svnURL.format(component), targetDir]
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            stdout = process.stdout.read()
            ret = process.wait()
            if ret != 0:
                raise SystemError("Failed to checkout repository (%d)" % process.returncode)
        else:
            gitURL = self.gitURL.format(self.getGITMapping(component))
            print('[{0}] GIT Clone: {1} into {2}'.format(self.version, gitURL, targetDir))
            repo = Repo.clone_from(gitURL, targetDir)

class LLVMArchiveHandler(LLVMResourceHandler):
    def __init__(self, version, rootDir, archiveDir, srcDir):
        self.version = version
        self.rootDir = rootDir
        self.archiveDir = archiveDir
        self.srcDir = srcDir
        self.baseURL = 'http://llvm.org/releases/{0}/'
        self.baseFileName = '{0}-{1}.src.tar.xz'

    def setupLLVMCore(self):
        if not LLVMResourceHandler.isComponentInstalled('llvm', self.rootDir):
            llvmArchive = self.downloadArchive('llvm', self.archiveDir)
            self.extractArchive(llvmArchive, self.srcDir, None, 1)
            LLVMResourceHandler.installComponent('llvm', self.rootDir)

    def setupComponent(self,component):
        if not LLVMResourceHandler.isComponentInstalled(component, self.rootDir):
            dependencies = LLVMResourceHandler.getComponentDepends(component)
            for c in dependencies:
                self.setupComponent(c)
            compArchive = self.downloadArchive(component, self.archiveDir)
            localName, localDir = LLVMResourceHandler.getComponentSpecs(component)
            self.extractArchive(compArchive, os.path.join(self.srcDir, localDir), localName)
            LLVMResourceHandler.installComponent(component, self.rootDir)

    def downloadArchive(self,component,archiveDir):
        fileName = self.baseFileName.format(component, self.version) 
        componentURL = self.baseURL.format(self.version) + fileName
        print('[{0}] Download archive {1} from {2}'.format(self.version, fileName, componentURL))
        archiveFileName = os.path.join(archiveDir, fileName)
        urllib.request.urlretrieve(componentURL, archiveFileName)
        return archiveFileName

    def extractArchive(self,archiveFile,srcDir,localDirName=None,strip = False):
        print('[{0}] Extract archive {1} into {2}'.format(self.version, archiveFile, srcDir))
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
@click.option('--llvm-repo', '-r', type=click.Choice(['svn','git']), default='svn')
@click.argument('target-directory', type=click.Path(True,False,True,True,True,True))
@click.argument('llvm-components', nargs=-1, type=click.Choice(['cfe', 'compiler-rt', 'libcxx', 'libcxxabi', 'libunwind', 'openmp', 'clang-tools-extra', 'lldb', 'test-suite']))
def main (**kwargs):
    rootDir = kwargs['target_directory']
    llvmVersions = kwargs['llvm_version']
    llvmComponents = kwargs['llvm_components']
    repoType = kwargs['llvm_repo']
    if len(llvmComponents) == 0:
        # download all
        llvmComponents = ['cfe', 'compiler-rt', 'libcxx', 'libcxxabi', 'libunwind', 'openmp', 'clang-tools-extra', 'lldb', 'test-suite']
    # setup LLVM
    for v in llvmVersions:
        targetDir = getTargetDirectory(rootDir, v)
        print('[{0}] Setting up LLVM'.format(v))
        dirs = setupTargetDirectory(targetDir)
        resourceHandler = LLVMResourceHandler.createHandler(v, targetDir, dirs['archive'], dirs['src'], repoType)
        resourceHandler.setupLLVMCore()
        for c in llvmComponents:
            print('[{0}] Setting up LLVM component {1}'.format(v, c))
            resourceHandler.setupComponent(c)

def getTargetDirectory(dir,version):
    return os.path.join(dir,version)

def setupTargetDirectory(dir):
    if os.path.exists(dir) and not LLVMResourceHandler.isLLVMResource(dir):
        raise RuntimeError('The target directory {0} already exists'.format(dir))
    elif not os.path.exists(dir):
        os.makedirs(dir)
        LLVMResourceHandler.setupLLVMResource(dir)
    targetDirs = { compDir : os.path.join(dir,compDir) for compDir in ['archive', 'build', 'install', 'src'] }
    for key,value in targetDirs.items():
        if not os.path.exists(value):
            os.makedirs(value)
    return targetDirs

if __name__ == '__main__':
    #try:
    main()
    #except Exception as e:
    #    print('Failed to setup LLVM: {0}'.format(e))
