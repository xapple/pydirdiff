# `pydirdiff` version 1.1.1

This tool compares two directories recursively and prints any differences found between them. This enables the easy verification of the integrity of backups for instance.

Typically you could approach this problem by using a special `rsync` command such as the following:

    rsync -archive --delete --verbose --dry-run --itemize-changes "$FIRST_DIR" "$SECND_DIR" | grep +++++

This method executes very quickly but the output is hard to read and understand. Pydirdiff, though slightly slower, is much better and clearer.

Here is a sample output:

    pydirdiff version 1.1.1 (pid 9586)
    Codebase at: <module 'pydirdiff' from 'pydirdiff/__init__.py'>
    The exact version of the codebase is: a7c04ad
    Start at: 2017-07-20 17:10:57.168819
    d /Volumes/Backup HD/.DocumentRevisions-V100                                                                                            Only in secnd
    d /Volumes/Backup HD/.Spotlight-V100                                                                                                    Only in secnd
    d /Volumes/Backup HD/.Trashes                                                                                                           Only in secnd
    d /Volumes/Original HD/.TemporaryItems                                                                                           Error: cannot access
    f /Volumes/Backup HD/.fseventsd/fc00755e6f0f84b9                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755e6f0f84ba                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755e6f07ed35                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755e6f07ef38                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755e6f07fdda                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755e6f07fddb                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755ea9df6d2f                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fc00755ea9df6d30                                                                                        Only in secnd
    f /Volumes/Backup HD/.fseventsd/fseventsd-uuid                                                                                          Only in secnd
    f /Volumes/Original HD/.fseventsd/no_log                                                                                                Only in first
    f /Volumes/Original HD/Documents/TODO.txt                                                                                         Diverge in contents
    f /Volumes/Original HD/Applications/Numbers.app/Contents/Resources/Templates/Shared/style-thumbail-Basic.tiff                    Diverge only in date
    d /Volumes/Backup HD/Documents/Music                                                                                                    Only in secnd
    f /Volumes/Original HD/Documents/Games/Emulation/MacOS/SheepShaver/Snow version/ROM                                              Diverge only in date
    f /Volumes/Original HD/Documents/Games/Emulation/MacOS/SheepShaver/Snow version/SheepShaver.app/Contents/MacOS/SheepShaver       Diverge only in date
    f /Volumes/Original HD/Documents/Pictures/Avatars/iChatIcons                                                                          Diverge in size

It works by comparing files pairs. If they both have the same size and dates they are assumed identical (instantaneous). If they have different sizes they are automatically flagged as different (instantaneous). If they have different dates (either creation or modification) but the same size in bytes, we compare their MD5 hashes to know the truth (both files are done in parallel but still slowish).

You can run this tool like this:

    $ pydirdiff/pydirdiff /Volumes/Original/ /Volumes/Copy/

Or to skip MD5 checksum and just look at sizes:

    $ pydirdiff/pydirdiff --cmp_fn=sizes_only /Volumes/Original/ /Volumes/Copy/

If you want to skip certain directories:

    $ pydirdiff/pydirdiff --ignore=".git" /Volumes/Original/ /Volumes/Copy/

`pydirdiff` will never write anything to disk, only read.

Possible improvements:

  * Detect file renames in a fuzzy and probabilistic way.
  * Detect directory renames and keep comparing contents if they match above a given threshold of Levenshtein distance.
  * When files have the same size and dates, instead of computing their complete hashes, we could have a function that starts running through both of them in async IO, and checks divergence every ten megabytes or so to avoid running through the whole files if they have a divergence already in the beginning. This would save some time in a few cases.