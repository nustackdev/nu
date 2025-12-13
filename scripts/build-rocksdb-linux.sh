#!/bin/bash
set -euo pipefail
set -x

# ==============================================================================
# BUILD ROCKSDB AND DEPENDENCIES FOR LINUX
# ==============================================================================
# This script builds RocksDB and all its compression library dependencies
# from source. It's designed to run in manylinux Docker containers.
#
# Dependencies built:
# - zlib (compression)
# - bzip2 (compression)
# - lz4 (compression)
# - zstd (compression)
# - snappy (compression)
# - RocksDB (main database library)
#
# All libraries are installed to $ESROCKS_DEP_DIR
# ==============================================================================

ROCKSDB_VERSION="${ROCKSDB_VERSION:-6.29.5}"
ESROCKS_DEP_DIR="${ESROCKS_DEP_DIR:-/tmp/esrocks_deps}"

mkdir -p "$ESROCKS_DEP_DIR"/{lib,include}
cd /tmp

echo "========================================="
echo "Building dependencies for Linux"
echo "Architecture: $(uname -m)"
echo "RocksDB version: $ROCKSDB_VERSION"
echo "Prefix: $ESROCKS_DEP_DIR"
echo "========================================="

# ==============================================================================
# Install build tools (if not present)
# ==============================================================================
if command -v yum &> /dev/null; then
    yum install -y curl gcc gcc-c++ make cmake3 patchelf || true
    ln -sf /usr/bin/cmake3 /usr/bin/cmake || true
elif command -v apt-get &> /dev/null; then
    apt-get update || true
    apt-get install -y curl gcc g++ make cmake patchelf || true
fi

# Compiler flags
export CFLAGS="-fPIC -O3"
export CXXFLAGS="-fPIC -O3"
export LDFLAGS="-Wl,-rpath,'\$ORIGIN'"
export PREFIX="$ESROCKS_DEP_DIR"

# ==============================================================================
# Build zlib
# ==============================================================================
echo "Building zlib..."
ZLIB_VERSION="1.3.1"
curl -L "https://www.zlib.net/zlib-${ZLIB_VERSION}.tar.gz" -o "zlib-${ZLIB_VERSION}.tar.gz"
tar xzf "zlib-${ZLIB_VERSION}.tar.gz"
cd "zlib-${ZLIB_VERSION}"
./configure --prefix="$PREFIX"
make -j$(nproc)
make install
cd /tmp && rm -rf "zlib-${ZLIB_VERSION}"*
echo "✓ zlib built"

# ==============================================================================
# Build bzip2
# ==============================================================================
echo "Building bzip2..."
BZIP2_VERSION="1.0.8"
curl -L "https://sourceware.org/pub/bzip2/bzip2-${BZIP2_VERSION}.tar.gz" -o "bzip2-${BZIP2_VERSION}.tar.gz"
tar xzf "bzip2-${BZIP2_VERSION}.tar.gz"
cd "bzip2-${BZIP2_VERSION}"
make clean >/dev/null 2>&1 || true
make CFLAGS="$CFLAGS"
make -f Makefile-libbz2_so CFLAGS="$CFLAGS"
make install PREFIX="$PREFIX"
cp -a libbz2.so* "$PREFIX/lib/" 2>/dev/null || true
cd /tmp && rm -rf "bzip2-${BZIP2_VERSION}"*
echo "✓ bzip2 built"

# ==============================================================================
# Build LZ4
# ==============================================================================
echo "Building LZ4..."
LZ4_VERSION="1.9.4"
curl -L "https://github.com/lz4/lz4/archive/v${LZ4_VERSION}.tar.gz" -o "lz4-${LZ4_VERSION}.tar.gz"
tar xzf "lz4-${LZ4_VERSION}.tar.gz"
cd "lz4-${LZ4_VERSION}"
make -j$(nproc) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"
cd /tmp && rm -rf "lz4-${LZ4_VERSION}"*
echo "✓ LZ4 built"

# ==============================================================================
# Build Zstandard
# ==============================================================================
echo "Building Zstandard..."
ZSTD_VERSION="1.5.6"
curl -L "https://github.com/facebook/zstd/releases/download/v${ZSTD_VERSION}/zstd-${ZSTD_VERSION}.tar.gz" -o "zstd-${ZSTD_VERSION}.tar.gz"
tar xzf "zstd-${ZSTD_VERSION}.tar.gz"
cd "zstd-${ZSTD_VERSION}"
make -j$(nproc) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"
cd /tmp && rm -rf "zstd-${ZSTD_VERSION}"*
echo "✓ Zstandard built"

# ==============================================================================
# Build Snappy
# ==============================================================================
echo "Building Snappy..."
SNAPPY_VERSION="1.2.1"
curl -L "https://github.com/google/snappy/archive/refs/tags/${SNAPPY_VERSION}.tar.gz" -o "snappy-${SNAPPY_VERSION}.tar.gz"
tar xzf "snappy-${SNAPPY_VERSION}.tar.gz"
cd "snappy-${SNAPPY_VERSION}"
rm -rf build
mkdir build
cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DSNAPPY_BUILD_TESTS=OFF \
    -DSNAPPY_BUILD_BENCHMARKS=OFF \
    -DSNAPPY_REQUIRE_ZLIB=OFF \
    -DSNAPPY_REQUIRE_LZO=OFF \
    -DSNAPPY_REQUIRE_LZ4=OFF \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
make -j$(nproc)
make install
cd /tmp && rm -rf "snappy-${SNAPPY_VERSION}"*
echo "✓ Snappy built"

# ==============================================================================
# Build RocksDB
# ==============================================================================
echo "Building RocksDB ${ROCKSDB_VERSION}..."
curl -L "https://github.com/facebook/rocksdb/archive/v${ROCKSDB_VERSION}.tar.gz" -o "rocksdb-${ROCKSDB_VERSION}.tar.gz"
tar xzf "rocksdb-${ROCKSDB_VERSION}.tar.gz"
cd "rocksdb-${ROCKSDB_VERSION}"

export LIBRARY_PATH="$PREFIX/lib"
export CPLUS_INCLUDE_PATH="$PREFIX/include"

make static_lib shared_lib -j$(nproc) \
    PORTABLE=1 \
    USE_RTTI=1 \
    DISABLE_WARNING_AS_ERROR=1 \
    DEBUG_LEVEL=0 \
    EXTRA_CXXFLAGS="$CXXFLAGS" \
    EXTRA_LDFLAGS="$LDFLAGS"

# Install
cp librocksdb.a "$PREFIX/lib/"
cp librocksdb.so* "$PREFIX/lib/" || true
cp -r include/rocksdb "$PREFIX/include/"

# Fix rpath on shared library so it can find its dependencies
# This makes the library self-contained without needing LD_LIBRARY_PATH
if command -v patchelf &> /dev/null; then
    echo "Setting rpath on librocksdb.so..."
    for lib in "$PREFIX/lib"/librocksdb.so*; do
        if [[ -f "$lib" && ! -L "$lib" ]]; then
            patchelf --set-rpath '$ORIGIN' "$lib" || true
        fi
    done
else
    echo "Warning: patchelf not found, skipping rpath fix"
    echo "Install with: yum install -y patchelf  OR  apt-get install -y patchelf"
fi

# Strip debug symbols
strip --strip-debug "$PREFIX/lib"/librocksdb.so* || true

cd /tmp && rm -rf "rocksdb-${ROCKSDB_VERSION}"*
echo "✓ RocksDB built successfully"

# ==============================================================================
# Verify
# ==============================================================================
echo "========================================="
echo "Build complete!"
echo "Libraries:"
ls -lh "$PREFIX/lib"/*.{a,so}* 2>/dev/null || true
echo "========================================="