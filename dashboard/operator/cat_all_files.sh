#!/bin/bash

# Set the destination file on the Windows 10 desktop
desktop_path="/mnt/c/Users/Alien/Desktop/concatenated_files.txt"

# Create or clear the destination file
> "$desktop_path"

# Recursively find and cat all files in the current directory
find / -type f -exec cat {} \; >> "$desktop_path"

echo "All files have been concatenated into $desktop_path"

