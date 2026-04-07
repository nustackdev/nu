"""Functional tests for Path ref.

Tests PathRef and PathSlot execution with real storage context.
"""

from pathlib import Path

from nu.stdlib.pathlib import PathI as PathRef


# ============================================================================
# PATH SET AND GET TESTS
# ============================================================================


class TestPathSetAndGet:
    """Test setting and getting path values through storage."""

    async def test_set_and_get_path(self, path_shape, ctx):
        """Set and retrieve a path value."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        result = await path_shape.config_path.execute(ctx)
        assert result == p

    async def test_set_path_from_string(self, path_shape, ctx):
        """Set path from string."""
        await path_shape.config_path.store("/home/user/file.txt").execute(ctx)
        result = await path_shape.config_path.execute(ctx)
        assert result == Path("/home/user/file.txt")

    async def test_set_multiple_paths(self, path_shape, ctx):
        """Set multiple path slots."""
        config = Path("/etc/config.json")
        data = Path("/var/data")

        await path_shape.config_path.store(config).execute(ctx)
        await path_shape.data_dir.store(data).execute(ctx)

        assert await path_shape.config_path.execute(ctx) == config
        assert await path_shape.data_dir.execute(ctx) == data


# ============================================================================
# PATH COMPONENT ACCESS TESTS
# ============================================================================


class TestPathComponentAccess:
    """Test accessing path components."""

    async def test_name(self, path_shape, ctx):
        """Access path name (final component)."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        assert await path_shape.config_path.name().execute(ctx) == "file.txt"

    async def test_stem(self, path_shape, ctx):
        """Access path stem (name without suffix)."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        assert await path_shape.config_path.stem().execute(ctx) == "file"

    async def test_suffix(self, path_shape, ctx):
        """Access path suffix (extension)."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        assert await path_shape.config_path.suffix().execute(ctx) == ".txt"

    async def test_suffixes(self, path_shape, ctx):
        """Access path suffixes for multi-extension files."""
        p = Path("/home/user/archive.tar.gz")
        await path_shape.config_path.store(p).execute(ctx)
        result = await path_shape.config_path.suffixes().execute(ctx)
        assert result == [".tar", ".gz"]

    async def test_parent(self, path_shape, ctx):
        """Access parent directory.

        Note: .parent() collides with Ref.parent property, so we compose
        via PathValue term wrapping instead of calling directly on the ref.
        """
        from nu.stdlib.pathlib import PathI as PathValue

        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        result = await PathValue.from_str(path_shape.config_path).parent().execute(ctx)
        assert result == Path("/home/user")

    async def test_parts(self, path_shape, ctx):
        """Access path parts."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        result = await path_shape.config_path.parts().execute(ctx)
        assert result == ("/", "home", "user", "file.txt")

    async def test_root(self, path_shape, ctx):
        """Access path root."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        assert await path_shape.config_path.root().execute(ctx) == "/"

    async def test_anchor(self, path_shape, ctx):
        """Access path anchor."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)
        assert await path_shape.config_path.anchor().execute(ctx) == "/"


# ============================================================================
# PATHREF CONSTRUCTOR TESTS
# ============================================================================


class TestPathRefConstructors:
    """Test PathRef constructors with execution."""

    async def test_from_str(self, ctx):
        """Create from string."""
        result = await PathRef.from_str("/home/user/file.txt").execute(ctx)
        assert result == Path("/home/user/file.txt")

    async def test_cwd(self, ctx):
        """Create from current working directory."""
        result = await PathRef.cwd().execute(ctx)
        assert result == Path.cwd()

    async def test_home(self, ctx):
        """Create from home directory."""
        result = await PathRef.home().execute(ctx)
        assert result == Path.home()


# ============================================================================
# PATH MANIPULATION TESTS
# ============================================================================


class TestPathManipulation:
    """Test path manipulation operations."""

    async def test_truediv_join(self, path_shape, ctx):
        """Join paths with / operator."""
        p = Path("/home/user")
        await path_shape.data_dir.store(p).execute(ctx)

        result = await (path_shape.data_dir / "subdir").execute(ctx)
        assert result == Path("/home/user/subdir")

    async def test_joinpath(self, path_shape, ctx):
        """Join paths with joinpath()."""
        p = Path("/home/user")
        await path_shape.data_dir.store(p).execute(ctx)

        result = await path_shape.data_dir.joinpath("subdir", "file.txt").execute(ctx)
        assert result == Path("/home/user/subdir/file.txt")

    async def test_with_name(self, path_shape, ctx):
        """Replace final component."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.with_name("other.txt").execute(ctx)
        assert result == Path("/home/user/other.txt")

    async def test_with_stem(self, path_shape, ctx):
        """Replace stem only."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.with_stem("other").execute(ctx)
        assert result == Path("/home/user/other.txt")

    async def test_with_suffix(self, path_shape, ctx):
        """Replace suffix only."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.with_suffix(".md").execute(ctx)
        assert result == Path("/home/user/file.md")

    async def test_relative_to(self, path_shape, ctx):
        """Get relative path."""
        p = Path("/home/user/project/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.relative_to("/home/user").execute(ctx)
        assert result == Path("project/file.txt")


# ============================================================================
# PATH TEST METHOD TESTS
# ============================================================================


class TestPathTests:
    """Test path test methods."""

    async def test_is_absolute_true(self, path_shape, ctx):
        """Check if path is absolute."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.is_absolute().execute(ctx)
        assert result is True

    async def test_is_absolute_false(self, path_shape, ctx):
        """Check if relative path is not absolute."""
        p = Path("./file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.is_absolute().execute(ctx)
        assert result is False

    async def test_is_relative_to_true(self, path_shape, ctx):
        """Check if path is relative to base."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.is_relative_to("/home").execute(ctx)
        assert result is True

    async def test_is_relative_to_false(self, path_shape, ctx):
        """Check if path is not relative to base."""
        p = Path("/var/log/app.log")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.is_relative_to("/home").execute(ctx)
        assert result is False

    async def test_match_true(self, path_shape, ctx):
        """Check if path matches pattern."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.match("*.txt").execute(ctx)
        assert result is True

    async def test_match_false(self, path_shape, ctx):
        """Check if path does not match pattern."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.match("*.py").execute(ctx)
        assert result is False


# ============================================================================
# PATH CONVERSION TESTS
# ============================================================================


class TestPathConversions:
    """Test path conversions."""

    async def test_as_posix(self, path_shape, ctx):
        """Convert to POSIX path string."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.as_posix().execute(ctx)
        assert result == "/home/user/file.txt"

    async def test_as_uri(self, path_shape, ctx):
        """Convert to file URI."""
        p = Path("/home/user/file.txt")
        await path_shape.config_path.store(p).execute(ctx)

        result = await path_shape.config_path.as_uri().execute(ctx)
        assert result == "file:///home/user/file.txt"


# ============================================================================
# PATH EQUALITY TESTS
# ============================================================================


class TestPathEquality:
    """Test path equality operations."""

    async def test_equals(self, path_shape, ctx):
        """Compare paths for equality."""
        await path_shape.config_path.store(Path("/home/user")).execute(ctx)
        await path_shape.data_dir.store(Path("/home/user")).execute(ctx)

        result = await path_shape.config_path.eq(path_shape.data_dir).execute(ctx)
        assert result is True

    async def test_not_equals(self, path_shape, ctx):
        """Compare paths for inequality."""
        await path_shape.config_path.store(Path("/home/user")).execute(ctx)
        await path_shape.data_dir.store(Path("/var/log")).execute(ctx)

        result = await path_shape.config_path.ne(path_shape.data_dir).execute(ctx)
        assert result is True
