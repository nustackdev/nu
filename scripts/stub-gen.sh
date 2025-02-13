#!/bin/bash

WS_ROOT="$(pwd)"
SRC_DIR="scriptable"

# Step 1: Delete all existing .pyi files recursively
echo "Deleting existing .pyi files..."
find "$SRC_DIR" -name "*.pyi" -type f -delete

# Step 2: Run stubgen (placeholder command)
echo "Running stubgen..."
stubgen -p scriptable  # -o "$SRC_DIR"  # to specify output directory
# ... Add more directories here to gen stubs

# Step 3: Remove .pyi files from specific directories
echo "Cleaning up unwanted stub files..."
DIRS_TO_CLEAN=(
    # "scriptable/example/example"
    # Add more directories here to clean up stubs
)

for dir in "${DIRS_TO_CLEAN[@]}"; do
    if [ -d "$SRC_DIR/$dir" ]; then
        echo "Cleaning stubs from $SRC_DIR/$dir"
        find "$SRC_DIR/$dir" -name "*.pyi" -type f -delete
    fi
done

# Step 4: Copy manually written stubs
# echo "Copying manual stubs..."
# if [ -d "scripts/stub-gen/stubs" ]; then
#     cd scripts/stub-gen/stubs
#     find . -name "*.pyi" -type f | while read stub_file; do
#         # Remove leading ./
#         rel_path=${stub_file#./}
#         # Create target directory if it doesn't exist
#         target_dir="$WS_ROOT/$SRC_DIR/$(dirname "$rel_path")"
#         mkdir -p "$target_dir"
#         # Copy the stub file
#         cp "$stub_file" "$target_dir/"
#         echo "Copied: $stub_file -> $target_dir/"
#     done
#     cd - > /dev/null
# fi

# Step 5: Run pre-commit to format the generated stubs
pre-commit run --all-files

echo "Done!"