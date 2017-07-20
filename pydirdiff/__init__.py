b'This module needs Python 2.7.x'

# Futures #
from __future__ import division

# Special variables #
__version__ = '1.0.0'
version_string = "pydirdiff version %s" % __version__

# Modules #
import sys, os
import pydirdiff
from plumbing.autopaths  import DirectoryPath
from plumbing.common     import md5sum, natural_sort
from plumbing.timer      import Timer

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
        # Time the pipeline execution #
        self.timer = Timer()
        self.timer.print_start()
        # Parallelism #
        self.set_up_parallelism()
        # Do it #
        self.check_directrory_pair(self.first_dir, self.secnd_dir)
        # End message #
        print "------------\nSuccess."
        self.timer.print_end()
        self.timer.print_total_elapsed()

    def set_up_parallelism(self):
        from multiprocessing import Pool
        self.pool = Pool(processes=2)

    def check_directrory_pair(self, root1, root2):
        """Just one directory. This is called recursively obviously."""
        # Get files and directories #
        files1, dirs1 = self.flat_contents(root1)
        files2, dirs2 = self.flat_contents(root2)
        # Files missing #
        missing = list(files1.symmetric_difference(files2))
        missing.sort(key=natural_sort)
        for f in missing:
            if f in files1: self.output(f, root1+'/'+f, 'f', "Only in first")
            else:           self.output(f, root2+'/'+f, 'f', "Only in second")
        # Directories missing #
        missing = list(dirs1.symmetric_difference(dirs2))
        missing.sort(key=natural_sort)
        for d in missing:
            if d in dirs1:  self.output(f, root1+'/'+f, 'd', "Only in first")
            else:           self.output(f, root2+'/'+f, 'd', "Only in second")
        # Files existing #
        existing = list(files1.intersection(files2))
        existing.sort(key=natural_sort)
        for f in existing:
            first  = root1+'/'+f
            second = root2+'/'+f
            # Size #
            if os.path.getsize(first) != os.path.getsize(second):
                self.output(f, first, 'f', 'Diverge in size')
                continue
            # Creation time #
            if os.path.getctime(first) != os.path.getctime(second):
                self.output(f, first, 'f', 'Diverge in creation date')
                continue
            # Modification time #
            if os.path.getmtime(first) != os.path.getmtime(second):
                sum1, sum2 = self.pool.apply_async(md5sum, [first, second])
                if sum1 != sum2:
                    self.output(f, first, 'f', 'Diverge in contents')
                    continue
                self.output(f, first, 'f', 'Diverge only in modification date')
        # Directories existing (recursion) #
        existing = list(dirs1.intersection(dirs2))
        existing.sort(key=natural_sort)
        for d in existing:
            first  = root1+'/'+d
            second = root2+'/'+d
            self.check_directrory_pair(first, second)

    def flat_contents(self, root):
        for root, dirs, files in os.walk(root): return set(f for f in files), set(d for d in dirs)

    def output(self, name, path, kind, status):
        print kind, path, status