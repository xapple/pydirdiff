b'This module needs Python 2.7.x'

# Futures #
from __future__ import division

# Special variables #
__version__ = '1.1.1'
version_string = "pydirdiff version %s" % __version__

# Modules #
import sys, os, re
from multiprocessing import Pool
import pydirdiff

# Maybe we don't have the plumbing library in our sys.path #
try: import plumbing
except ImportError: sys.path.insert(0, '/repos/plumbing/')

# First party modules #
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
    """The main object.
    Possible to dos:
    - Detect file renames.
    - Detect directory renames and keep comparing contents.
    """

    def __repr__(self): return '<Analysis object on "%s" and "%s">' % \
                        (self.first_dir, self.secnd_dir)

    def __init__(self, first_dir, secnd_dir,
                 checksum      = 'md5',
                 skip_dsstore  = True,
                 skip_dates    = True,
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
        self.count = 0

    def run(self):
        """A method to run the whole comparison."""
        # Intro messages #
        print version_string + " (pid %i)" % os.getpid()
        print "Codebase at: %s" % pydirdiff
        if git_repo: print "The exact version of the codebase is: " + git_repo.short_hash
        # Time the pipeline execution #
        self.timer = Timer()
        self.timer.print_start()
        # Recap both directories #
        print "------------"
        print 'First directory: "%s"' % self.first_dir
        print 'Secnd directory: "%s"' % self.secnd_dir
        # Set up the parallelism #
        self.pool = Pool(processes=2)
        # Get and update the terminal length #
        self.rows, self.columns = map(int, os.popen('stty size', 'r').read().split())
        # Do it #
        self.compare_two_dirs(self.first_dir.rstrip('/'), self.secnd_dir.rstrip('/'))
        # Clear scanning line at the end #
        if self.verbose:
            sys.stdout.write('\r\n')
            sys.stdout.flush()
        # Special message #
        if self.count == 0:
            print Color.bold + "The two directories were perfectly identical." + Color.end
        # End message #
        print "\n------------\nSuccess."
        self.timer.print_end()
        self.timer.print_total_elapsed()

    def compare_two_dirs(self, root1, root2):
        """Just one directory pair. This is called recursively obviously."""
        # Print "Scanning" #
        if self.verbose: self.print_current_dir(root1)
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
        files1, dirs1 = contents1
        files2, dirs2 = contents2
        # Filter the stupid .DS_Store files #
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
                    try:
                        sum1, sum2 = self.pool.map_async(md5sum, (first, secnd)).get(sys.maxint)
                    except IOError:
                        self.output(f, first, 'f', "Error: cannot read")
                        continue
                    if sum1 != sum2:
                        self.output(f, first, 'f', 'Diverge in contents')
                        continue
                if not self.skip_dates: self.output(f, first, 'f', 'Diverge only in date')
        # Directories existing #
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
            # Normal case (recursion) #
            self.compare_two_dirs(first, secnd)

    def flat_contents(self, root):
        for root, dirs, files in os.walk(root):
            return set(f for f in files), set(d for d in dirs)

    status_to_color = {
        'first'   : Color.f_cyn,
        'secnd'   : Color.f_pur,
        'content' : Color.f_ylw,
        'size'    : Color.f_ylw,
        'date'    : Color.f_wht,
        'Symbolic': Color.f_ylw,
        'Error'   : Color.ylw + Color.flash + Color.f_red
    }

    def output(self, name, path, kind, status):
        """Every difference is either displayed or cataloged by calling
        this method from `self.compare_two_dirs()`.
        One has to be careful with file and directory paths, they are
        essentially uncontrolled user input. Don't use str.format() because
        it can throw KeyError if a filename contains `{` and `}`.
        A path can even contain the character `\r` erasing the line you
        just printed, so sanitize everything."""
        # Record #
        self.count += 1
        # Give color to different messages #
        for keyword in self.status_to_color:
            if keyword in status:
                color = self.status_to_color.get(keyword)
                break
        else: color = Color.f_grn
        # Sanitize input #
        loc = re.sub("(\s)", lambda m: repr(m.group(0)).strip("'"), path)
        loc = loc.decode('utf-8')
        # Build string to print #
        string = u'(%s) ' % kind
        string = string + loc
        string = string + max(1, self.columns - len(string) - len(status)) * ' '
        string = string + color + status + Color.end
        # Remove the scanning line first #
        if self.verbose:
            sys.stdout.write('\r')
            sys.stdout.flush()
        # Print #
        print string

    def print_current_dir(self, directory):
        """If verbosity is turned on, display the current directory
        that is being scanned, and then print '\r' to show the next."""
        # Verbose (can't have line longer than terminal size) #
        string = '{:%i.%i}' % (self.columns-10, self.columns-10)
        string = string.format(directory)
        sys.stdout.write('\r' + Color.bold + 'Scanning: ' + Color.end + string)
        sys.stdout.flush()
