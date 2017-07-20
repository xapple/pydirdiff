This tool compares two directories recursively and prints any differences.

This enables the verification of the integrity of backups for instance.

It's much better than doing a (though it's much slower):

    rsync -archive --delete --verbose --dry-run --itemize-changes "$FIRST_DIR" "$SECND_DIR"

Here is a sample output:

    pydirdiff version 1.1.0 (pid 9586)
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