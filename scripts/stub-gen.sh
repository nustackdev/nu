#!/bin/bash

WS_ROOT="$(pwd)"
STUBS_DIR="$WS_ROOT/stubs"

# Step 1: Delete all existing .pyi files recursively
echo "Deleting existing stubs files..."
rm -r "$STUBS_DIR"

# Step 2: Run stubgen (placeholder command)
echo "Running stubgen..."
stubgen -p loomi  -o "$STUBS_DIR"
stubgen -p loomistd  -o "$STUBS_DIR"
stubgen -p loomiverse  -o "$STUBS_DIR"

mv "$STUBS_DIR/loomi" "$STUBS_DIR/loomi_stubs"
mv "$STUBS_DIR/loomistd" "$STUBS_DIR/loomistd_stubs"
mv "$STUBS_DIR/loomiverse" "$STUBS_DIR/loomiverse_stubs"

# Step 3: Remove .pyi files from specific directories
echo "Cleaning up unwanted stub files..."
DIRS_TO_CLEAN=(
    # "loomi/example/example"
    # Add more directories here to clean up stubs
)

for dir in "${DIRS_TO_CLEAN[@]}"; do
    if [ -d "$SRC_DIR/$dir" ]; then
        echo "Cleaning stubs from $SRC_DIR/$dir"
        find "$SRC_DIR/$dir" -name "*.pyi" -type f -delete
    fi
done


# Step 4: Run pre-commit to format the generated stubs
pre-commit run --all-files

echo "Done!"