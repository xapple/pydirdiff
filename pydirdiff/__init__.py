b'This module needs Python 2.7.x'

# Futures #
from __future__ import division

# Special variables #
__version__ = '1.3.0'
version_string = "pydirdiff version %s" % __version__

# Modules #
import sys, os
import pydirdiff
from plumbing.autopaths import DirectoryPath

# Find the data dir #
module     = sys.modules[__name__]
module_dir = os.path.dirname(module.__file__) + '/'
repos_dir  = os.path.abspath(module_dir + '../') + '/'

# If we are in dev mode it's a git repo #
if os.path.exists(repos_dir + '.git/'): git_repo = GitRepo(repos_dir)
else:                                   git_repo = None

################################################################################
class Analysis(object):
    """The main object."""

    def __repr__(self): return '<Analysis object on "%s" and "%s">' % \
                        (self.first_dir, self.secnd_dir)

    def __init__(self, first_dir, secnd_dir,
                 checksum      = 'md5',
                ):
        # Base parameters #
        self.first_dir = DirectoryPath(first_dir)
        self.secnd_dir = DirectoryPath(secnd_dir)
        # Check #
        self.first_dir.must_exist()
        self.secnd_dir.must_exist()

    def run(self):
        """A method to run the whole comparison."""
        print version_string + " (pid %i)" % os.getpid()
        print "Codebase at: %s" % pydirdiff
        if git_repo: print "The exact version of the codebase is: " + git_repo.short_hash
        # Timer #
        self.timer.print_start()
        # Do it #
        self.check_directrory_pair(self.first_dir, self.secnd_dir)
        # End message #
        print "------------\nSuccess."
        self.timer.print_end()
        self.timer.print_total_elapsed()

    def flat_files(self, d):
        for root, dirs, files in os.walk(d): return set(os.path.join(root, f) for f in files)

    def flat_directories(self, d):
        for root, dirs, files in os.walk(d): return set(os.path.join(root, d) for d in dirs)

    def check_directrory_pair(self):
        """Just one directory. This is called recursively obviously."""
        # Get files and directories #
        files1, files2 = self.first_dir.flat_files,       self.secnd_dir.flat_files
        dirs1,  dirs2  = self.first_dir.flat_directories, self.secnd_dir.flat_directories
        # Files missing #
        missing = set(files1).symmetric_difference(set(files2))
        for f in missing:
            if f in files1: self.output(f, 'f', "Only in first")
            else:           self.output(f, 'f', "Only in second")
        # Directories missing #
        missing = set(dirs1).symmetric_difference(set(dirs2))
        for d in missing:
            if d in files1: self.output(d, 'd', "Only in first")
            else:           self.output(d, 'd', "Only in second")
        # Files existing #
        files = set(files1).intersection(set(files2))
        for f in files:

        # Directories existing (recursion) #
        dirs = set(dirs1).intersection(set(dirs2))
        for d in dirs: self.check_directrory_pair(d, d)

    def output(self, path, kind, status):
        print kind, path, status