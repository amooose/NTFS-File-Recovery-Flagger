# NTFS-File-Recovery-Flagger
A python script that finds and reflags deleted files as active by manually reading and parsing the Master File Table.

# Requirements
Pywin32 and elevate

# Usage
1. Run the file with the one argument being your drive letter, (C,D,E,F,G..) 
2. Once the deleted files are found, you will prompted to continue, which will then    
set the flags of all deleted files as active, and run chkdsk DRIVELETTER: /f to recover all orphaned files.
