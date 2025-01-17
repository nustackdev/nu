#!/bin/bash

# Usage:
# - Without any filters: ./git-stats.sh
# - To include only specific file extensions: ./git-stats.sh -i "js,py,cpp"
# - To exclude specific files: ./git-stats.sh -e "README.md,LICENSE"
# - Combine both: ./git-stats.sh -i "js,py" -e "config.js"

# Default values
include_extensions=""
exclude_files=""

# Parse command line arguments
while getopts "i:e:" opt; do
  case $opt in
    i) include_extensions=$OPTARG ;;
    e) exclude_files=$OPTARG ;;
    *) echo "Usage: $0 [-i include_extensions] [-e exclude_files]" >&2
       exit 1 ;;
  esac
done

# Prepare git ls-files command
git_command="git ls-files"

# Add extension filter
if [ -n "$include_extensions" ]; then
  extensions=$(echo $include_extensions | sed 's/,/\\|/g')
  git_command="$git_command | grep -E '\\.($extensions)$'"
fi

# Add file exclusion filter
if [ -n "$exclude_files" ]; then
  exclusions=$(echo $exclude_files | sed 's/,/|/g')
  git_command="$git_command | grep -Ev '($exclusions)'"
fi

# Execute git command and store results
files=$(eval $git_command)

# Count files and lines
file_count=$(echo "$files" | wc -l)
total_lines=$(echo "$files" | xargs wc -l 2>/dev/null | tail -n 1 | awk '{print $1}')

echo "Total committed files: $file_count"
echo "Total lines of code: $total_lines"
