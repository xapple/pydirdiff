b'This module needs Python 2.7.x'

# Futures #
from __future__ import division

# Special variables #
__version__ = '1.1.0'
version_string = "pydirdiff version %s" % __version__

# Modules #
import sys, os
import pydirdiff
from plumbing.git        import GitRepo
from plumbing.autopaths  import DirectoryPath
from plumbing.common     import md5sum, natural_sort
from plumbing.timer      import Timer
from plumbing.color      import Color

# Find the dir #
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
                 skip_dsstore  = True,
                 skip_dates    = False,
                 verbose       = True,
                ):
        # Base parameters #
        self.first_dir = DirectoryPath(first_dir)
        self.secnd_dir = DirectoryPath(secnd_dir)
        # Check #
        self.first_dir.must_exist()
        self.secnd_dir.must_exist()
        # Attributes #
        self.checksum     = checksum
        self.skip_dsstore = skip_dsstore
        self.skip_dates   = skip_dates
        self.verbose      = verbose
        # Other #
        self.no_differences = True

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
        # Get and update the terminal length #
        self.rows, self.columns = map(int, os.popen('stty size', 'r').read().split())
        # Do it #
        self.check_directrory_pair(self.first_dir.rstrip('/'), self.secnd_dir.rstrip('/'))
        # End message #
        if self.verbose:
            sys.stdout.write('\r')
            sys.stdout.flush()
        if self.no_differences:
            print Color.bold + "The two directories were perfectly identical." + Color.end
        print "\n------------\nSuccess."
        self.timer.print_end()
        self.timer.print_total_elapsed()

    def set_up_parallelism(self):
        """TODO: python multiprocessing keyboard interrupt"""
        from multiprocessing import Pool
        self.pool = Pool(processes=2)


            # process item here
    def check_directrory_pair(self, root1, root2):
        """Just one directory. This is called recursively obviously."""
        # Verbose (can't have line longer than terminal size) #
        if self.verbose:
            string = '{:%i.%i}' % (self.columns-10, self.columns-10)
            string = string.format(root1)
            sys.stdout.write('\r' + Color.bold + 'Scanning: ' + Color.end + string)
            sys.stdout.flush()
        # Get contents #
        contents1 = self.flat_contents(root1)
        contents2 = self.flat_contents(root2)
        # Check #
        if contents1 is None:
            self.output(os.path.basename(root1), root1, 'd', "Error: cannot access")
            return
        if contents2 is None:
            self.output(os.path.basename(root2), root2, 'd', "Error: cannot access")
            return
        # Split files and directories #
        files1, dirs1 = self.flat_contents(root1)
        files2, dirs2 = self.flat_contents(root2)
        # Filter the DS_Store #
        if self.skip_dsstore:
            files1.discard(".DS_Store")
            files2.discard(".DS_Store")
        # Files missing #
        missing = list(files1.symmetric_difference(files2))
        missing.sort(key=natural_sort)
        for f in missing:
            if f in files1: self.output(f, root1+'/'+f, 'f', "Only in first")
            else:           self.output(f, root2+'/'+f, 'f', "Only in secnd")
        # Directories missing #
        missing = list(dirs1.symmetric_difference(dirs2))
        missing.sort(key=natural_sort)
        for d in missing:
            if d in dirs1:  self.output(d, root1+'/'+d, 'd', "Only in first")
            else:           self.output(d, root2+'/'+d, 'd', "Only in secnd")
        # Files existing #
        existing = list(files1.intersection(files2))
        existing.sort(key=natural_sort)
        for f in existing:
            first = root1 + '/' + f
            secnd = root2 + '/' + f
            # Possible permission denied (first) #
            try: stat1 = os.lstat(first)
            except OSError:
                self.output(f, first, 'f', "Error: cannot stat")
                continue
            # Possible permission denied (second) #
            try: stat2 = os.lstat(secnd)
            except OSError:
                self.output(f, secnd, 'f', "Error: cannot stat")
                continue
            # Size #
            if stat1.st_size != stat2.st_size:
                self.output(f, first, 'f', 'Diverge in size')
                continue
            # Modification and creation time #
            if (stat1.st_mtime != stat2.st_mtime) or (stat1.st_ctime != stat2.st_ctime):
                # Special symlink case #
                if os.path.islink(first):
                    if os.readlink(first) != os.readlink(secnd):
                        self.output(f, first, 's', 'Symbolic file divergence')
                        continue
                # Checksum #
                else:
                    sum1, sum2 = self.pool.map(md5sum, (first, secnd))
                    if sum1 != sum2:
                        self.output(f, first, 'f', 'Diverge in contents')
                        continue
                if not self.skip_dates: self.output(f, first, 'f', 'Diverge only in date')
        # Directories existing (recursion) #
        existing = list(dirs1.intersection(dirs2))
        existing.sort(key=natural_sort)
        for d in existing:
            first = root1 + '/' + d
            secnd = root2 + '/' + d
            # Special symlink case #
            if os.path.islink(first):
                if os.readlink(first) != os.readlink(secnd):
                    self.output(d, first, 's', 'Symbolic dir divergence')
                continue
            # Normal case #
            self.check_directrory_pair(first, secnd)

    def flat_contents(self, root):
        for root, dirs, files in os.walk(root):
            return set(f for f in files), set(d for d in dirs)

    def output(self, name, path, kind, status):
        if   'first'    in status:   color = Color.f_cyn
        elif 'secnd'    in status:   color = Color.f_pur
        elif 'content'  in status:   color = Color.f_ylw
        elif 'size'     in status:   color = Color.f_ylw
        elif 'date'     in status:   color = Color.f_wht
        elif 'Symbolic' in status:   color = Color.f_ylw
        elif 'Error'    in status:   color = Color.ylw + Color.flash + Color.f_red
        else:                        color = Color.f_grn
        # String #
        string = kind + ' ' + path + ' ' +  "{0:>{1}}"
        string = string.format(color + status, max(1, self.columns - len(string) + 13))
        string = string + Color.end
        # Print #
        if self.verbose:
            sys.stdout.write('\r')
            sys.stdout.flush()
        print string
        # Record #
        self.no_differences = False