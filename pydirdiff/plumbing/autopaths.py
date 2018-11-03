# Built-in modules #
import os, stat, tempfile, subprocess, shutil, codecs, gzip
import glob, warnings, zipfile

# Internal modules #
from pydirdiff.plumbing.common import md5sum, natural_sort

# Third party modules #
import sh

################################################################################
class DirectoryPath(str):

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.path)

    @classmethod
    def clean_path(cls, path):
        """Given a path, return a cleaned up version for initialization."""
        # Conserve 'None' object style #
        if path is None: return None
        # Don't nest DirectoryPaths or the like #
        if hasattr(path, 'path'): path = path.path
        # Expand the tilda #
        if "~" in path: path = os.path.expanduser(path)
        # Our standard is to end with a slash for directories #
        if not path.endswith('/'): path += '/'
        # Return the result #
        return path

    def __new__(cls, path, *args, **kwargs):
        """A DirectoryPath is in fact a string"""
        return str.__new__(cls, cls.clean_path(path))

    def __init__(self, path):
        self.path = self.clean_path(path)

    def __add__(self, other):
        if other.endswith("/"): return DirectoryPath(self.path + other)
        else:                   return FilePath(self.path + other)

    def __iter__(self): return self.flat_contents

    @property
    def name(self):
        """Just the directory name"""
        return os.path.basename(os.path.dirname(self.path))

    @property
    def prefix_path(self):
        """The full path without the extension"""
        return os.path.splitext(self.path)[0].rstrip('/')

    @property
    def absolute_path(self):
        """The absolute path starting with a `/`"""
        return os.path.abspath(self.path) + '/'

    @property
    def directory(self):
        """The full path of the directory containing this one."""
        return DirectoryPath(os.path.dirname(os.path.dirname(self.path)))

    #-------------------------- Recursive contents ---------------------------#
    @property
    def contents(self):
        """The files and directories in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for d in dirs:  yield DirectoryPath(os.path.join(root, d))
            for f in files: yield FilePath(os.path.join(root, f))

    @property
    def files(self):
        """The files in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for f in files: yield FilePath(os.path.join(root, f))

    @property
    def directories(self):
        """The directories in this directory, recursively."""
        for root, dirs, files in os.walk(self.path, topdown=False):
            for d in dirs: yield DirectoryPath(os.path.join(root, d))

    #----------------------------- Flat contents -----------------------------#
    @property
    def flat_contents(self):
        """The files and directories in this directory non-recursively."""
        for root, dirs, files in os.walk(self.path):
            for d in dirs:  yield DirectoryPath(os.path.join(root, d))
            for f in files: yield FilePath(os.path.join(root, f))
            break

    @property
    def flat_files(self):
        """The files in this directory non-recursively, and sorted.
        #TODO: check for permission denied in directory."""
        for root, dirs, files in os.walk(self.path):
            result = [FilePath(os.path.join(root, f)) for f in files]
            break
        result.sort(key=lambda x: natural_sort(x.path))
        return result

    @property
    def flat_directories(self):
        """The directories in this directory non-recursively, and sorted."""
        for root, dirs, files in os.walk(self.path):
            result = [DirectoryPath(os.path.join(root, d)) for d in dirs]
            break
        result.sort(key=lambda x: natural_sort(x.path))
        return result

    #-------------------------------- Other ----------------------------------#
    @property
    def is_symlink(self):
        """Is this directory a symbolic link to an other directory?"""
        return os.path.islink(self.path.rstrip('/'))

    @property
    def exists(self):
        """Does it exist in the file system?"""
        return os.path.lexists(self.path) # Include broken symlinks

    @property
    def empty(self):
        """Does the directory contain no files?"""
        return len(list(self.flat_contents)) == 0

    @property
    def permissions(self):
        """Convenience object for dealing with permissions."""
        return FilePermissions(self.path)

    @property
    def mod_time(self):
        """The modification time"""
        return os.stat(self.path).st_mtime

    @property
    def size(self):
        """The total size in bytes of all file contents."""
        return Filesize(sum(f.count_bytes for f in self.files))

    #------------------------------- Methods ---------------------------------#
    def must_exist(self):
        """Raise an exception if the directory doesn't exist."""
        if not os.path.isdir(self.path):
            raise Exception("The directory path '%s' does not exist." % self.path)

    def remove(self):
        if not self.exists: return False
        if self.is_symlink: return self.remove_when_symlink()
        shutil.rmtree(self.path, ignore_errors=True)
        return True

    def remove_when_symlink(self):
        if not self.exists: return False
        os.remove(self.path.rstrip('/'))
        return True

    def create(self, safe=False, inherit=True):
        # Create it #
        if not safe:
            os.makedirs(self.path)
            if inherit: os.chmod(self.path, self.directory.permissions.number)
        if safe:
            try:
                os.makedirs(self.path)
                if inherit: os.chmod(self.path, self.directory.permissions.number)
            except OSError: pass

    def create_if_not_exists(self):
        if not self.exists: self.create()

    def zip(self, keep_orig=False):
        """Make a zip archive of the directory"""
        shutil.make_archive(self.prefix_path , "zip", self.directory, self.name)
        if not keep_orig: self.remove()

    def link_from(self, where, safe=False):
        """Make a link here pointing to another directory somewhere else.
        The destination is hence self.path and the source is *where*"""
        if not safe:
            self.remove()
            return os.symlink(where, self.path.rstrip('/'))
        if safe:
            try: self.remove()
            except OSError: pass
            try: os.symlink(where, self.path.rstrip('/'))
            except OSError: warnings.warn("Symlink of %s to %s did not work" % (where, self))

    def copy(self, path):
        assert not os.path.exists(path)
        shutil.copytree(self.path, path)

    def glob(self, pattern):
        """Perform a glob search in this directory."""
        files = glob.glob(self.path + pattern)
        return map(FilePath, files)

    def find(self, pattern):
        """Find a file in this directory."""
        f = glob.glob(self.path + pattern)[0]
        return FilePath(f)

################################################################################
class FilePath(str):
    """I can never remember all those darn `os.path` commands, so I made a class
    that wraps them with an easier and more pythonic syntax.

        path = FilePath('/home/root/text.txt')
        print path.extension
        print path.directory
        print path.filename

    You can find lots of the common things you would need to do with file paths.
    Such as: path.make_executable() etc etc."""

    def __repr__(self):    return '<%s object "%s">' % (self.__class__.__name__, self.path)

    def __nonzero__(self): return self.path != None and self.count_bytes != 0

    def __list__(self):    return self.count

    def __iter__(self):
        with open(self.path, 'r') as handle:
            for line in handle: yield line

    def __len__(self):
        if self.path is None: return 0
        return self.count

    def __new__(cls, path, *args, **kwargs):
        """A FilePath is in fact a string."""
        return str.__new__(cls, cls.clean_path(path))

    def __init__(self, path):
        self.path = self.clean_path(path)

    def __add__(self, other):
        if other.endswith("/"): return DirectoryPath(self.path + other)
        else:                   return FilePath(self.path + other)

    def __sub__(self, directory):
        """Subtract a directory from the current path to get the relative path
        of the current file from that directory."""
        return os.path.relpath(self.path, directory)

    @classmethod
    def clean_path(cls, path):
        """Given a path, return a cleaned up version for initialization."""
        # Conserve None object style #
        if path is None: return None
        # Don't nest FilePaths or the like #
        if hasattr(path, 'path'): path = path.path
        # Expand tilda #
        if "~" in path: path = os.path.expanduser(path)
        # Expand star #
        if "*" in path:
            matches = glob.glob(path)
            if len(matches) < 1: raise Exception("Found exactly no files matching '%s'" % path)
            if len(matches) > 1: raise Exception("Found several files matching '%s'" % path)
            path = matches[0]
        # Return the result #
        return path

    @property
    def first(self):
        """Just the first line. Don't try this on binary files."""
        with open(self.path, 'r') as handle:
            for line in handle: return line

    @property
    def exists(self):
        """Does it exist in the file system."""
        return os.path.lexists(self.path) # Returns True even for broken symbolic links

    @property
    def prefix_path(self):
        """The full path without the (last) extension and trailing period."""
        return str(os.path.splitext(self.path)[0])

    @property
    def prefix(self):
        """Just the filename without the (last) extension and trailing period."""
        return str(os.path.basename(self.prefix_path))

    @property
    def short_prefix(self):
        """Just the filename without any extension or periods."""
        return self.filename.split('.')[0]

    @property
    def filename(self):
        """Just the filename with the extension."""
        return str(os.path.basename(self.path))

    @property
    def directory(self):
        """The directory containing this file."""
        # The built-in function #
        directory = os.path.dirname(self.path)
        # Maybe we need to go the absolute path way #
        if not directory: directory = os.path.dirname(self.absolute_path)
        # Return #
        return DirectoryPath(directory + '/')

    @property
    def extension(self):
        """The extension with the leading period."""
        return os.path.splitext(self.path)[1]

    @property
    def count_bytes(self):
        """The number of bytes."""
        if not self.exists: return 0
        return os.path.getsize(self.path)

    @property
    def count(self):
        """We are going to default to the number of lines."""
        return int(sh.wc('-l', self.path).split()[0])

    @property
    def size(self):
        """Human readable file size."""
        return Filesize(self.count_bytes)

    @property
    def permissions(self):
        """Convenience object for dealing with permissions."""
        return FilePermissions(self.path)

    @property
    def contents(self):
        """The contents as a string."""
        with open(self.path, 'r') as handle: return handle.read()

    @property
    def absolute_path(self):
        """The absolute path starting with a `/`."""
        return FilePath(os.path.abspath(self.path))

    @property
    def physical_path(self):
        """The physical path like in `pwd -P`."""
        return FilePath(os.path.realpath(self.path))

    @property
    def relative_path(self):
        """The relative path when compared with current directory."""
        return FilePath(os.path.relpath(self.physical_path))

    @property
    def mdate(self):
        """Return the modification date."""
        return os.path.getmtime(self.path)

    @property
    def cdate(self):
        """Return the modification date."""
        return os.path.getctime(self.path)

    @property
    def md5(self):
        """Return the md5 checksum."""
        return md5sum(self.path)

    @property
    def might_be_binary(self):
        """Try to quickly guess if the file is binary."""
        from binaryornot.check import is_binary
        return is_binary(self.path)

    @property
    def contains_binary(self):
        """Return True if the file contains binary characters."""
        from binaryornot.helpers import is_binary_string
        return is_binary_string(self.contents)

    #-------------------------------- Methods --------------------------------#
    def read(self, encoding=None):
        with codecs.open(self.path, 'r', encoding) as handle: content = handle.read()
        return content

    def create(self):
        if not self.directory.exists: self.directory.create()
        self.open('w')
        return self

    def open(self, mode='r'):
        self.handle = open(self.path, mode)
        return self.handle

    def add_str(self, string):
        self.handle.write(string)

    def close(self):
        self.handle.close()

    def write(self, content, encoding=None):
        if encoding is None:
            with open(self.path, 'w') as handle: handle.write(content)
        else:
            with codecs.open(self.path, 'w', encoding) as handle: handle.write(content)

    def writelines(self, content, encoding=None):
        if encoding is None:
            with open(self.path, 'w') as handle: handle.writelines(content)
        else:
            with codecs.open(self.path, 'w', encoding) as handle: handle.writelines(content)

    def remove(self):
        if not self.exists: return False
        os.remove(self.path)
        return True

    def copy(self, path):
        # Directory special case #
        if path.endswith('/'): path += self.filename
        # Normal case #
        shutil.copy2(self.path, path)

    def execute(self):
        return subprocess.call([self.path])

    def replace_extension(self, new_extension='txt'):
        """Return a new path with the extension swapped out."""
        return FilePath(os.path.splitext(self.path)[0] + '.' + new_extension)

    def new_name_insert(self, string):
        """Return a new name by appending a string before the extension."""
        return self.prefix_path + "." + string + self.extension

    def make_directory(self):
        """Create the directory the file is supposed to be in if it does not exist."""
        if not self.directory.exists: self.directory.create()

    def must_exist(self):
        """Raise an exception if the path doesn't exist."""
        if not self.exists: raise Exception("The file path '%s' does not exist." % self.path)

    def head(self, lines=10):
        """Return the first few lines."""
        content = FilePath.__iter__(self)
        for x in xrange(lines):
            yield content.next()

    def move_to(self, path):
        """Move the file."""
        # Special directory case, keep the same name (put it inside) #
        if path.endswith('/'): path = path + self.filename
        # Normal case #
        assert not os.path.exists(path)
        shutil.move(self.path, path)
        # Update the internal link #
        self.path = path

    def rename(self, new_name):
        """Rename the file but leave it in the same directory."""
        assert '/' not in new_name
        path = self.directory + new_name
        assert not os.path.exists(path)
        shutil.move(self.path, path)
        # Update the internal link #
        self.path = path

    def link_from(self, path, safe=False):
        """Make a link here pointing to another file somewhere else.
        The destination is hence self.path and the source is *path*."""
        # Get source and destination #
        source      = path
        destination = self.path
        # Do it #
        if not safe:
            if os.path.exists(destination): os.remove(destination)
            os.symlink(source, destination)
        # Do it safely #
        if safe:
            try: os.remove(destination)
            except OSError: pass
            try: os.symlink(source, destination)
            except OSError: pass

    def link_to(self, path, safe=False, absolute=True):
        """Create a link somewhere else pointing to this file.
        The destination is hence *path* and the source is self.path."""
        # If source is a file and the destination is a dir, put it inside #
        if path.endswith('/'): path = path + self.filename
        # Get source and destination #
        if absolute: source = self.absolute_path
        else:        source = self.path
        destination = path
        # Do it #
        if not safe:
            if os.path.exists(destination): os.remove(destination)
            os.symlink(source, destination)
        # Do it safely #
        if safe:
            try: os.remove(destination)
            except OSError: pass
            try: os.symlink(source, destination)
            except OSError: pass

    def gzip_to(self, path=None):
        """Make a gzipped version of the file at a given path."""
        if path is None: path = self.path + ".gz"
        with open(self.path, 'rb') as orig_file:
            with gzip.open(path, 'wb') as new_file:
                new_file.writelines(orig_file)
        return FilePath(path)

    def ungzip_to(self, path=None, mode='w'):
        """Make an unzipped version of the file at a given path."""
        if path is None: path = self.path[:3]
        with gzip.open(self, 'rb') as orig_file:
            with open(path, mode) as new_file:
                new_file.writelines(orig_file)
        return FilePath(path)

    def unzip_to(self, destination=None, inplace=False, single=True):
        """Unzip a standard zip file. Can specify the destination of the
        uncompressed file, or just set inplace=True to delete the original."""
        # Check #
        assert zipfile.is_zipfile(self.path)
        # Load #
        z = zipfile.ZipFile(self.path)
        if single or inplace: assert len(z.infolist()) == 1
        # Single file #
        if single:
            member = z.infolist()[0]
            tmpdir = tempfile.mkdtemp() + '/'
            z.extract(member, tmpdir)
            z.close()
            if inplace: shutil.move(tmpdir + member.filename, self.directory + member.filename)
            else:       shutil.move(tmpdir + member.filename, destination)
        # Multifile - no security, dangerous - Will use CWD if dest is None!! #
        # If a file starts with an absolute path, will overwrite your files anywhere #
        if not single:
            z.extractall(destination)

    def untargz_to(self, destination=None, inplace=False):
        """Make an untargzipped version of the file at a given path"""
        import tarfile
        archive = tarfile.open(self.path, 'r:gz')
        archive.extractall(destination)

################################################################################
class Filesize(object):
    """
    Container for a size in bytes with a human readable representation
    Use it like this:

        >>> size = Filesize(123123123)
        >>> print size
        '117.4 MiB'
    """

    precisions = [0, 0, 1, 2, 2, 2]

    def __init__(self, size, system='decimal'):
        # Record the size #
        self.size = size
        # Pick the system used #
        if system is 'binary':
            self.chunk = 1024
            self.units = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
        elif system is 'decimal':
            self.chunk = 1000
            self.units = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
        else:
            raise Exception("Unrecognized file size system '%s'" % system)

    def __eq__(self, other):
        return self.size == other

    def __str__(self):
        if self.size == 0: return '0 bytes'
        from math import log
        unit = self.units[min(int(log(self.size, self.chunk)), len(self.units) - 1)]
        return self.format(unit)

    def format(self, unit):
        # Input checking #
        if unit not in self.units: raise Exception("Not a valid file size unit: '%s'" % unit)
        # Special no plural case #
        if self.size == 1 and unit == 'bytes': return '1 byte'
        # Compute #
        exponent      = self.units.index(unit)
        quotient      = float(self.size) / self.chunk**exponent
        precision     = self.precisions[exponent]
        format_string = '{:.%sf} {}' % (precision)
        # Return a string #
        return format_string.format(quotient, unit)

################################################################################
class FilePermissions(object):
    """Container for reading and setting a files permissions."""

    def __init__(self, path):
        self.path = path

    @property
    def number(self):
        """The permission bits as an octal integer."""
        return os.stat(self.path).st_mode & 0o0777

    def make_executable(self):
        return os.chmod(self.path, os.stat(self.path).st_mode | stat.S_IEXEC)

    def only_readable(self):
        """Remove all writing privileges."""
        return os.chmod(self.path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
