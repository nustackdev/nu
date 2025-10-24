#!/bin/bash
set -e
set -x

# ==============================================================================
# BUILD ROCKSDB AND DEPENDENCIES FOR MACOS
# ==============================================================================
# Similar to Linux script but with macOS-specific configurations:
# - Uses .dylib instead of .so
# - Uses install_name_tool for library paths
# - Supports universal binaries (x86_64 + arm64)
# ==============================================================================

ROCKSDB_VERSION="${ROCKSDB_VERSION:-9.7.3}"
RWROCKS_DEP_DIR="${RWROCKS_DEP_DIR:-/tmp/rwrocks_deps}"

mkdir -p "$RWROCKS_DEP_DIR"/{lib,include}
cd /tmp

echo "========================================="
echo "Building dependencies for macOS"
echo "Architecture: $(uname -m)"
echo "Deployment target: $MACOSX_DEPLOYMENT_TARGET"
echo "========================================="

# Detect architecture
ARCH=$(uname -m)  # arm64 or x86_64

# Compiler flags for macOS
export CFLAGS="-fPIC -O3 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14}"
export CXXFLAGS="-fPIC -O3 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14} -stdlib=libc++"
export LDFLAGS="-mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14} -stdlib=libc++"
export PREFIX="$RWROCKS_DEP_DIR"

# ==============================================================================
# Build dependencies (same as Linux, but .dylib output)
# ==============================================================================

# zlib
echo "Building zlib..."
ZLIB_VERSION="1.3.1"
curl -L "https://www.zlib.net/zlib-${ZLIB_VERSION}.tar.gz" -o "zlib-${ZLIB_VERSION}.tar.gz"
tar xzf "zlib-${ZLIB_VERSION}.tar.gz"
cd "zlib-${ZLIB_VERSION}"
./configure --prefix="$PREFIX"
make -j$(sysctl -n hw.ncpu)
make install
cd /tmp && rm -rf "zlib-${ZLIB_VERSION}"*
echo "✓ zlib built"

# bzip2
echo "Building bzip2..."
BZIP2_VERSION="1.0.8"
curl -L "https://sourceware.org/pub/bzip2/bzip2-${BZIP2_VERSION}.tar.gz" -o "bzip2-${BZIP2_VERSION}.tar.gz"
tar xzf "bzip2-${BZIP2_VERSION}.tar.gz"
cd "bzip2-${BZIP2_VERSION}"
make -f Makefile-libbz2_so CFLAGS="$CFLAGS"
make install PREFIX="$PREFIX"
cd /tmp && rm -rf "bzip2-${BZIP2_VERSION}"*
echo "✓ bzip2 built"

# LZ4
echo "Building LZ4..."
LZ4_VERSION="1.9.4"
curl -L "https://github.com/lz4/lz4/archive/v${LZ4_VERSION}.tar.gz" -o "lz4-${LZ4_VERSION}.tar.gz"
tar xzf "lz4-${LZ4_VERSION}.tar.gz"
cd "lz4-${LZ4_VERSION}"
make -j$(sysctl -n hw.ncpu) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"
cd /tmp && rm -rf "lz4-${LZ4_VERSION}"*
echo "✓ LZ4 built"

# Zstandard
echo "Building Zstandard..."
ZSTD_VERSION="1.5.6"
curl -L "https://github.com/facebook/zstd/releases/download/v${ZSTD_VERSION}/zstd-${ZSTD_VERSION}.tar.gz" -o "zstd-${ZSTD_VERSION}.tar.gz"
tar xzf "zstd-${ZSTD_VERSION}.tar.gz"
cd "zstd-${ZSTD_VERSION}"
make -j$(sysctl -n hw.ncpu) PREFIX="$PREFIX"
make install PREFIX="$PREFIX"
cd /tmp && rm -rf "zstd-${ZSTD_VERSION}"*
echo "✓ Zstandard built"

# Snappy
echo "Building Snappy..."
SNAPPY_VERSION="1.2.1"
curl -L "https://github.com/google/snappy/archive/refs/tags/${SNAPPY_VERSION}.tar.gz" -o "snappy-${SNAPPY_VERSION}.tar.gz"
tar xzf "snappy-${SNAPPY_VERSION}.tar.gz"
cd "snappy-${SNAPPY_VERSION}"
mkdir build && cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DSNAPPY_BUILD_TESTS=OFF
make -j$(sysctl -n hw.ncpu)
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

make static_lib shared_lib -j$(sysctl -n hw.ncpu) \
    PORTABLE=1 \
    USE_RTTI=1 \
    DEBUG_LEVEL=0 \
    EXTRA_CXXFLAGS="$CXXFLAGS" \
    EXTRA_LDFLAGS="$LDFLAGS"

# Install
cp librocksdb.a "$PREFIX/lib/"
cp librocksdb.*.dylib "$PREFIX/lib/" || true
cp -r include/rocksdb "$PREFIX/include/"

# Fix library install names (macOS-specific)
# This ensures the .dylib can be found at runtime
for dylib in "$PREFIX/lib"/librocksdb.*.dylib; do
    if [ -f "$dylib" ]; then
        install_name_tool -id "@rpath/$(basename $dylib)" "$dylib"
    fi
done

# Strip debug symbols
strip -S "$PREFIX/lib"/librocksdb.*.dylib || true

cd /tmp && rm -rf "rocksdb-${ROCKSDB_VERSION}"*
echo "✓ RocksDB built successfully"

# ==============================================================================
# Verify
# ==============================================================================
echo "========================================="
echo "Build complete!"
echo "Libraries:"
ls -lh "$PREFIX/lib"/*.{a,dylib} 2>/dev/null || true
echo "========================================="