#!/bin/bash
set -e  # Exit on error
set -x  # Print commands (for debugging)

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

# Configuration
ROCKSDB_VERSION="${ROCKSDB_VERSION:-9.7.3}"
ESROCKS_DEP_DIR="${ESROCKS_DEP_DIR:-/tmp/esrocks_deps}"

# Create directories
mkdir -p "$ESROCKS_DEP_DIR"/{lib,include}
cd /tmp

echo "========================================="
echo "Building dependencies in: $ESROCKS_DEP_DIR"
echo "RocksDB version: $ROCKSDB_VERSION"
echo "========================================="

# ==============================================================================
# Install build tools (if not present)
# ==============================================================================
if command -v yum &> /dev/null; then
    # RHEL/CentOS based (manylinux)
    yum install -y wget gcc gcc-c++ make cmake3 || true
    ln -sf /usr/bin/cmake3 /usr/bin/cmake || true
elif command -v apt-get &> /dev/null; then
    # Debian/Ubuntu based
    apt-get update
    apt-get install -y wget gcc g++ make cmake
fi

# Common compiler flags
export CFLAGS="-fPIC -O3"
export CXXFLAGS="-fPIC -O3"
export PREFIX="$ESROCKS_DEP_DIR"

# ==============================================================================
# Build zlib (compression library)
# ==============================================================================
echo "Building zlib..."
ZLIB_VERSION="1.3.1"
wget -q "https://www.zlib.net/zlib-${ZLIB_VERSION}.tar.gz"
tar xzf "zlib-${ZLIB_VERSION}.tar.gz"
cd "zlib-${ZLIB_VERSION}"

./configure --prefix="$PREFIX" --static
make -j$(nproc)
make install

cd /tmp
rm -rf "zlib-${ZLIB_VERSION}" "zlib-${ZLIB_VERSION}.tar.gz"
echo "✓ zlib built successfully"

# ==============================================================================
# Build bzip2 (compression library)
# ==============================================================================
echo "Building bzip2..."
BZIP2_VERSION="1.0.8"
wget -q "https://sourceware.org/pub/bzip2/bzip2-${BZIP2_VERSION}.tar.gz"
tar xzf "bzip2-${BZIP2_VERSION}.tar.gz"
cd "bzip2-${BZIP2_VERSION}"

# bzip2 doesn't have a configure script, edit Makefile
make -f Makefile-libbz2_so CFLAGS="$CFLAGS"
make install PREFIX="$PREFIX"

cd /tmp
rm -rf "bzip2-${BZIP2_VERSION}" "bzip2-${BZIP2_VERSION}.tar.gz"
echo "✓ bzip2 built successfully"

# ==============================================================================
# Build LZ4 (compression library)
# ==============================================================================
echo "Building LZ4..."
LZ4_VERSION="1.9.4"
wget -q "https://github.com/lz4/lz4/archive/v${LZ4_VERSION}.tar.gz" -O "lz4-${LZ4_VERSION}.tar.gz"
tar xzf "lz4-${LZ4_VERSION}.tar.gz"
cd "lz4-${LZ4_VERSION}"

make -j$(nproc) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"

cd /tmp
rm -rf "lz4-${LZ4_VERSION}" "lz4-${LZ4_VERSION}.tar.gz"
echo "✓ LZ4 built successfully"

# ==============================================================================
# Build Zstandard (compression library)
# ==============================================================================
echo "Building Zstandard..."
ZSTD_VERSION="1.5.6"
wget -q "https://github.com/facebook/zstd/releases/download/v${ZSTD_VERSION}/zstd-${ZSTD_VERSION}.tar.gz"
tar xzf "zstd-${ZSTD_VERSION}.tar.gz"
cd "zstd-${ZSTD_VERSION}"

make -j$(nproc) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"

cd /tmp
rm -rf "zstd-${ZSTD_VERSION}" "zstd-${ZSTD_VERSION}.tar.gz"
echo "✓ Zstandard built successfully"

# ==============================================================================
# Build Snappy (compression library)
# ==============================================================================
echo "Building Snappy..."
SNAPPY_VERSION="1.2.1"
wget -q "https://github.com/google/snappy/archive/refs/tags/${SNAPPY_VERSION}.tar.gz" -O "snappy-${SNAPPY_VERSION}.tar.gz"
tar xzf "snappy-${SNAPPY_VERSION}.tar.gz"
cd "snappy-${SNAPPY_VERSION}"

mkdir build && cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DSNAPPY_BUILD_TESTS=OFF \
    -DSNAPPY_BUILD_BENCHMARKS=OFF

make -j$(nproc)
make install

cd /tmp
rm -rf "snappy-${SNAPPY_VERSION}" "snappy-${SNAPPY_VERSION}.tar.gz"
echo "✓ Snappy built successfully"

# ==============================================================================
# Build RocksDB (main database library)
# ==============================================================================
echo "Building RocksDB ${ROCKSDB_VERSION}..."
wget -q "https://github.com/facebook/rocksdb/archive/v${ROCKSDB_VERSION}.tar.gz" -O "rocksdb-${ROCKSDB_VERSION}.tar.gz"
tar xzf "rocksdb-${ROCKSDB_VERSION}.tar.gz"
cd "rocksdb-${ROCKSDB_VERSION}"

# RocksDB build configuration
# PORTABLE=1: Build for generic CPU (not optimized for build machine)
# USE_RTTI=1: Enable RTTI (needed for some features)
# DEBUG_LEVEL=0: Release build (optimized, no debug symbols)
export LIBRARY_PATH="$PREFIX/lib"
export CPLUS_INCLUDE_PATH="$PREFIX/include"

make static_lib shared_lib -j$(nproc) \
    PORTABLE=1 \
    USE_RTTI=1 \
    DEBUG_LEVEL=0 \
    EXTRA_CXXFLAGS="-fPIC" \
    EXTRA_CFLAGS="-fPIC"

# Install libraries and headers
cp librocksdb.a "$PREFIX/lib/"
cp librocksdb.so* "$PREFIX/lib/" || true
cp -r include/rocksdb "$PREFIX/include/"

# Strip debug symbols to reduce size
strip --strip-debug "$PREFIX/lib/librocksdb.so" || true

cd /tmp
rm -rf "rocksdb-${ROCKSDB_VERSION}" "rocksdb-${ROCKSDB_VERSION}.tar.gz"
echo "✓ RocksDB built successfully"

# ==============================================================================
# Verify build
# ==============================================================================
echo "========================================="
echo "Build complete! Verifying..."
echo "========================================="
echo "Libraries in $PREFIX/lib:"
ls -lh "$PREFIX/lib" | grep -E '\.(so|a)$'
echo ""
echo "Headers in $PREFIX/include:"
ls -d "$PREFIX/include"/* 2>/dev/null || echo "No headers found"
echo "========================================="