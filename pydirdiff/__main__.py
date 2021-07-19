#!/usr/bin/env python

"""
An example from the command line is the following:

    $ ipython3 -i -m pydirdiff -- /Volumes/FirstCopy/Files/Music /Volumes/SecondCopy/Files/Music --ignore='.git' --ignore='-Dump-' --cmp_fn='sizes_only'
"""

# Built-in modules #
import sys, argparse
from argparse import RawTextHelpFormatter

if __name__ == '__main__':

    # Maybe we don't have the pydirdiff library in our sys.path #
    try: import pydirdiff
    except ImportError: sys.path.insert(0, '/repos/pydirdiff/')
    import pydirdiff
    from pydirdiff.plumbing.common import flatter

    # Make a shell arguments parser #
    desc = pydirdiff.version_string
    parser = argparse.ArgumentParser(description=desc, formatter_class=RawTextHelpFormatter)

    # All the required arguments #
    parser.add_argument("first_dir", help="The first directory to process", type=str)
    parser.add_argument("secnd_dir", help="The second directory to process", type=str)

    # All the optional arguments #
    parameters = {
        "cmp_fn"        : "Either `md5` or `sizes_only`. Defaults to `md5`.",
        "skip_dsstore"  : "Ignore all '.DS_Store' files. Either `True` or `False`. Defaults to `True`.",
        "skip_dates"    : "Don't print files that just differ in dates. Either `True` or `False`. Defaults to `True`.",
        "verbose"       : "Display current directory as search progresses. Either `True` or `False`. Defaults to `True`.",
    }

    # Add parameters #
    for param, hlp in parameters.items(): parser.add_argument("--" + param, help=hlp)

    # Add multiple ignores #
    parser.add_argument('--ignore', help="Ignore any directories with this name. Defaults to `None`.",
                        action='append', nargs='*')

    # Get arguments #
    args      = parser.parse_args()
    first_dir = args.first_dir
    secnd_dir = args.secnd_dir

    # All the other parameters #
    kwargs = {k:getattr(args, k) for k in parameters if getattr(args, k) is not None}

    # Take care of multiple ignores #
    kwargs['ignore'] = flatter(args.ignore)

    # Run the pipeline #
    pydirdiff.Analysis(first_dir, secnd_dir, **kwargs).run()
