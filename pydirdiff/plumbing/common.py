# -*- coding: utf-8 -*-

# Built-in modules #
import re, hashlib, unicodedata

# One liners #
flatter = lambda x: [item for sublist in x for item in sublist]

################################################################################
def sanitize_text(text):
    """Make a safe representation of a string.
    Note: the `\s` special character matches any whitespace character.
    This is equivalent to the set [\t\n\r\f\v] as well as ` ` (whitespace)."""
    # First replace characters that have specific effects with their repr #
    text = re.sub("(\s)", lambda m: repr(m.group(0)).strip("'"), text)
    # Make it a unicode string (the try supports python 2 and 3) #
    try: text = text.decode('utf-8')
    except AttributeError: pass
    # Normalize it “
    text = unicodedata.normalize('NFC', text)
    return text

###############################################################################
def natural_sort(item):
    """
    Sort strings that contain numbers correctly. Works in Python 2 and 3.

    >>> l = ['v1.3.12', 'v1.3.3', 'v1.2.5', 'v1.2.15', 'v1.2.3', 'v1.2.1']
    >>> l.sort(key=natural_sort)
    >>> l.__repr__()
    "['v1.2.1', 'v1.2.3', 'v1.2.5', 'v1.2.15', 'v1.3.3', 'v1.3.12']"
    """
    dre = re.compile(r'(\d+)')
    return [int(s) if s.isdigit() else s.lower() for s in re.split(dre, item)]

################################################################################
def md5sum(file_path, blocksize=65536):
    """Compute the md5 of a file. Pretty fast."""
    result = hashlib.md5()
    with open(file_path, "rb") as f:
        chunk = f.read(blocksize)
        while chunk:
            result.update(chunk)
            chunk = f.read(blocksize)
    return result.hexdigest()