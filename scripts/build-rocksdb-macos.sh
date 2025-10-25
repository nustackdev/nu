#!/bin/bash
set -euo pipefail
set -x

# ==============================================================================
# BUILD ROCKSDB AND DEPENDENCIES FOR MACOS
# ==============================================================================
# Similar to Linux script but with macOS-specific configurations:
# - Uses .dylib instead of .so
# - Uses install_name_tool for library paths
# - Supports universal binaries (x86_64 + arm64)
# ==============================================================================

ROCKSDB_VERSION="${ROCKSDB_VERSION:-6.29.5}"
RWROCKS_DEP_DIR="${RWROCKS_DEP_DIR:-/tmp/rwrocks_deps}"

mkdir -p "$RWROCKS_DEP_DIR"/{lib,include}
cd /tmp

echo "========================================="
echo "Building dependencies for macOS"
echo "Architecture: $(uname -m)"
echo "Deployment target: ${MACOSX_DEPLOYMENT_TARGET:-}"
echo "========================================="

# Detect architecture
ARCH=$(uname -m)  # arm64 or x86_64

# Compiler flags for macOS
export CFLAGS="-fPIC -O3 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14}"
export CXXFLAGS="-fPIC -O3 -mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14} -stdlib=libc++"
export LDFLAGS="-mmacosx-version-min=${MACOSX_DEPLOYMENT_TARGET:-10.14} -stdlib=libc++"
export PREFIX="$RWROCKS_DEP_DIR"

fix_install_id() {
    local lib_path="$1"
    if [[ -f "$lib_path" ]]; then
        install_name_tool -id "@rpath/$(basename "$lib_path")" "$lib_path"
    fi
}

rewrite_dep_rpath() {
    local target="$1"
    shift || true
    if [[ ! -f "$target" ]]; then
        return
    fi
    for dep_name in "$@"; do
        local dep_path="$PREFIX/lib/$dep_name"
        if [[ -f "$dep_path" ]]; then
            install_name_tool -change "$dep_path" "@rpath/$dep_name" "$target"
        fi
    done
}

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
ZLIB_DYLIB=$(find "$PREFIX/lib" -maxdepth 1 -name 'libz.*.*.dylib' -print -quit || true)
if [[ -n "${ZLIB_DYLIB:-}" ]]; then
    fix_install_id "$ZLIB_DYLIB"
fi
cd /tmp && rm -rf "zlib-${ZLIB_VERSION}"*
echo "✓ zlib built"

# bzip2
echo "Building bzip2..."
BZIP2_VERSION="1.0.8"
curl -L "https://sourceware.org/pub/bzip2/bzip2-${BZIP2_VERSION}.tar.gz" -o "bzip2-${BZIP2_VERSION}.tar.gz"
tar xzf "bzip2-${BZIP2_VERSION}.tar.gz"
cd "bzip2-${BZIP2_VERSION}"
BZIP2_SONAME="libbz2.1.0"
BZIP2_DYLIB="libbz2.1.0.${BZIP2_VERSION##*.}.dylib"
make clean >/dev/null 2>&1 || true
make CFLAGS="$CFLAGS"
# Create shared library manually for macOS
clang -dynamiclib \
    $LDFLAGS \
    -current_version "${BZIP2_VERSION}" \
    -compatibility_version "1.0" \
    -install_name "@rpath/${BZIP2_SONAME}.dylib" \
    blocksort.o huffman.o crctable.o randtable.o compress.o decompress.o bzlib.o \
    -o "${BZIP2_DYLIB}"
ln -sf "${BZIP2_DYLIB}" "${BZIP2_SONAME}.dylib"
ln -sf "${BZIP2_DYLIB}" "libbz2.dylib"
install -m 0755 "${BZIP2_DYLIB}" "$PREFIX/lib/"
ln -sf "${BZIP2_DYLIB}" "$PREFIX/lib/${BZIP2_SONAME}.dylib"
ln -sf "${BZIP2_DYLIB}" "$PREFIX/lib/libbz2.dylib"
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
LZ4_DYLIB=$(find "$PREFIX/lib" -maxdepth 1 -name 'liblz4.*.dylib' -print -quit || true)
if [[ -n "${LZ4_DYLIB:-}" ]]; then
    fix_install_id "$LZ4_DYLIB"
fi
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
ZSTD_DYLIB=$(find "$PREFIX/lib" -maxdepth 1 -name 'libzstd.*.dylib' -print -quit || true)
if [[ -n "${ZSTD_DYLIB:-}" ]]; then
    fix_install_id "$ZSTD_DYLIB"
fi
cd /tmp && rm -rf "zstd-${ZSTD_VERSION}"*
echo "✓ Zstandard built"

# Snappy
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
make -j$(sysctl -n hw.ncpu)
make install
SNAPPY_DYLIB=$(find "$PREFIX/lib" -maxdepth 1 -name 'libsnappy.*.dylib' -print -quit || true)
if [[ -n "${SNAPPY_DYLIB:-}" ]]; then
    fix_install_id "$SNAPPY_DYLIB"
fi
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
    DISABLE_WARNING_AS_ERROR=1 \
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

DEPENDENCY_RPATH_LIBS=(
    "libsnappy.1.dylib"
    "libz.1.dylib"
    "libbz2.1.0.dylib"
    "liblz4.1.dylib"
    "libzstd.1.dylib"
)
for dylib in "$PREFIX/lib"/librocksdb.*.dylib; do
    rewrite_dep_rpath "$dylib" "${DEPENDENCY_RPATH_LIBS[@]}"
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
