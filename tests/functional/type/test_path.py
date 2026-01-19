"""Functional tests for Path type.

Tests PathType and PathSlot execution with real storage context.
"""

from pathlib import Path

from everybase.type import PathType


# ============================================================================
# PATH SET AND GET TESTS
# ============================================================================


class TestPathSetAndGet:
    """Test setting and getting path values through storage."""

    def test_set_and_get_path(self, path_shape, ctx):
        """Set and retrieve a path value."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        result = path_shape.config_path.get().execute(ctx)
        assert result == p

    def test_set_path_from_string(self, path_shape, ctx):
        """Set path from string."""
        path_shape.config_path.set("/home/user/file.txt").execute(ctx)
        result = path_shape.config_path.get().execute(ctx)
        assert result == Path("/home/user/file.txt")

    def test_set_multiple_paths(self, path_shape, ctx):
        """Set multiple path slots."""
        config = Path("/etc/config.json")
        data = Path("/var/data")

        path_shape.config_path.set(config).execute(ctx)
        path_shape.data_dir.set(data).execute(ctx)

        assert path_shape.config_path.get().execute(ctx) == config
        assert path_shape.data_dir.get().execute(ctx) == data


# ============================================================================
# PATH COMPONENT ACCESS TESTS
# ============================================================================


class TestPathComponentAccess:
    """Test accessing path components."""

    def test_name(self, path_shape, ctx):
        """Access path name (final component)."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        assert path_shape.config_path.name().execute(ctx) == "file.txt"

    def test_stem(self, path_shape, ctx):
        """Access path stem (name without suffix)."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        assert path_shape.config_path.stem().execute(ctx) == "file"

    def test_suffix(self, path_shape, ctx):
        """Access path suffix (extension)."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        assert path_shape.config_path.suffix().execute(ctx) == ".txt"

    def test_suffixes(self, path_shape, ctx):
        """Access path suffixes for multi-extension files."""
        p = Path("/home/user/archive.tar.gz")
        path_shape.config_path.set(p).execute(ctx)
        result = path_shape.config_path.suffixes().execute(ctx)
        assert result == [".tar", ".gz"]

    def test_parent(self, path_shape, ctx):
        """Access parent directory."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        result = path_shape.config_path.parent().execute(ctx)
        assert result == Path("/home/user")

    def test_parts(self, path_shape, ctx):
        """Access path parts."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        result = path_shape.config_path.parts().execute(ctx)
        assert result == ("/", "home", "user", "file.txt")

    def test_root(self, path_shape, ctx):
        """Access path root."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        assert path_shape.config_path.root().execute(ctx) == "/"

    def test_anchor(self, path_shape, ctx):
        """Access path anchor."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)
        assert path_shape.config_path.anchor().execute(ctx) == "/"


# ============================================================================
# PATHTYPE CONSTRUCTOR TESTS
# ============================================================================


class TestPathTypeConstructors:
    """Test PathType constructors with execution."""

    def test_from_str(self, ctx):
        """Create from string."""
        result = PathType.from_str("/home/user/file.txt").execute(ctx)
        assert result == Path("/home/user/file.txt")

    def test_cwd(self, ctx):
        """Create from current working directory."""
        result = PathType.cwd().execute(ctx)
        assert result == Path.cwd()

    def test_home(self, ctx):
        """Create from home directory."""
        result = PathType.home().execute(ctx)
        assert result == Path.home()


# ============================================================================
# PATH MANIPULATION TESTS
# ============================================================================


class TestPathManipulation:
    """Test path manipulation operations."""

    def test_truediv_join(self, path_shape, ctx):
        """Join paths with / operator."""
        p = Path("/home/user")
        path_shape.data_dir.set(p).execute(ctx)

        result = (path_shape.data_dir.get() / "subdir").execute(ctx)
        assert result == Path("/home/user/subdir")

    def test_joinpath(self, path_shape, ctx):
        """Join paths with joinpath()."""
        p = Path("/home/user")
        path_shape.data_dir.set(p).execute(ctx)

        result = path_shape.data_dir.joinpath("subdir", "file.txt").execute(ctx)
        assert result == Path("/home/user/subdir/file.txt")

    def test_with_name(self, path_shape, ctx):
        """Replace final component."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.get().with_name("other.txt").execute(ctx)
        assert result == Path("/home/user/other.txt")

    def test_with_stem(self, path_shape, ctx):
        """Replace stem only."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.get().with_stem("other").execute(ctx)
        assert result == Path("/home/user/other.txt")

    def test_with_suffix(self, path_shape, ctx):
        """Replace suffix only."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.get().with_suffix(".md").execute(ctx)
        assert result == Path("/home/user/file.md")

    def test_relative_to(self, path_shape, ctx):
        """Get relative path."""
        p = Path("/home/user/project/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.get().relative_to("/home/user").execute(ctx)
        assert result == Path("project/file.txt")


# ============================================================================
# PATH TEST METHOD TESTS
# ============================================================================


class TestPathTests:
    """Test path test methods."""

    def test_is_absolute_true(self, path_shape, ctx):
        """Check if path is absolute."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.is_absolute().execute(ctx)
        assert result is True

    def test_is_absolute_false(self, path_shape, ctx):
        """Check if relative path is not absolute."""
        p = Path("./file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.is_absolute().execute(ctx)
        assert result is False

    def test_is_relative_to_true(self, path_shape, ctx):
        """Check if path is relative to base."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.is_relative_to("/home").execute(ctx)
        assert result is True

    def test_is_relative_to_false(self, path_shape, ctx):
        """Check if path is not relative to base."""
        p = Path("/var/log/app.log")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.is_relative_to("/home").execute(ctx)
        assert result is False

    def test_match_true(self, path_shape, ctx):
        """Check if path matches pattern."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.match("*.txt").execute(ctx)
        assert result is True

    def test_match_false(self, path_shape, ctx):
        """Check if path does not match pattern."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.match("*.py").execute(ctx)
        assert result is False


# ============================================================================
# PATH CONVERSION TESTS
# ============================================================================


class TestPathConversions:
    """Test path conversions."""

    def test_as_posix(self, path_shape, ctx):
        """Convert to POSIX path string."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.as_posix().execute(ctx)
        assert result == "/home/user/file.txt"

    def test_as_uri(self, path_shape, ctx):
        """Convert to file URI."""
        p = Path("/home/user/file.txt")
        path_shape.config_path.set(p).execute(ctx)

        result = path_shape.config_path.as_uri().execute(ctx)
        assert result == "file:///home/user/file.txt"


# ============================================================================
# PATH EQUALITY TESTS
# ============================================================================


class TestPathEquality:
    """Test path equality operations."""

    def test_equals(self, path_shape, ctx):
        """Compare paths for equality."""
        path_shape.config_path.set(Path("/home/user")).execute(ctx)
        path_shape.data_dir.set(Path("/home/user")).execute(ctx)

        result = (path_shape.config_path.get() == path_shape.data_dir.get()).execute(ctx)
        assert result is True

    def test_not_equals(self, path_shape, ctx):
        """Compare paths for inequality."""
        path_shape.config_path.set(Path("/home/user")).execute(ctx)
        path_shape.data_dir.set(Path("/var/log")).execute(ctx)

        result = (path_shape.config_path.get() != path_shape.data_dir.get()).execute(ctx)
        assert result is True
