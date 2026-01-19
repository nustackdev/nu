"""Unit tests for Path type.

Tests for:
- PathType (constructors, operations, methods)
"""

from everybase.type.path import PathType
from everyterm.ops import DivOp, FuncCallOp
from everyterm.types import BoolType, ListType, StrType, TupleType


# =============================================================================
# PATHTYPE CONSTRUCTION TESTS
# =============================================================================


class TestPathTypeConstruction:
    """PathType construction tests."""

    def test_from_str(self):
        """Create from string."""
        pt = PathType.from_str("/home/user/file.txt")
        assert isinstance(pt, PathType)
        assert isinstance(pt.source, FuncCallOp)

    def test_cwd(self):
        """Create from current working directory."""
        pt = PathType.cwd()
        assert isinstance(pt, PathType)

    def test_home(self):
        """Create from home directory."""
        pt = PathType.home()
        assert isinstance(pt, PathType)


# =============================================================================
# PATHTYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestPathTypeAccessors:
    """PathType component accessor tests."""

    def test_name_returns_strtype(self):
        """name() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.name()
        assert isinstance(result, StrType)

    def test_stem_returns_strtype(self):
        """stem() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.stem()
        assert isinstance(result, StrType)

    def test_suffix_returns_strtype(self):
        """suffix() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.suffix()
        assert isinstance(result, StrType)

    def test_suffixes_returns_listtype(self):
        """suffixes() returns ListType."""
        pt = PathType.from_str("/home/user/file.tar.gz")
        result = pt.suffixes()
        assert isinstance(result, ListType)

    def test_parent_returns_pathtype(self):
        """parent() returns PathType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.parent()
        assert isinstance(result, PathType)

    def test_parents_returns_tupletype(self):
        """parents() returns TupleType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.parents()
        assert isinstance(result, TupleType)

    def test_root_returns_strtype(self):
        """root() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.root()
        assert isinstance(result, StrType)

    def test_anchor_returns_strtype(self):
        """anchor() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.anchor()
        assert isinstance(result, StrType)

    def test_parts_returns_tupletype(self):
        """parts() returns TupleType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.parts()
        assert isinstance(result, TupleType)


# =============================================================================
# PATHTYPE MANIPULATION TESTS
# =============================================================================


class TestPathTypeManipulation:
    """PathType manipulation tests."""

    def test_truediv_returns_pathtype(self):
        """/ operator returns PathType."""
        pt = PathType.from_str("/home/user")
        result = pt / "subdir"
        assert isinstance(result, PathType)
        assert isinstance(result.source, DivOp)

    def test_joinpath_returns_pathtype(self):
        """joinpath() returns PathType."""
        pt = PathType.from_str("/home/user")
        result = pt.joinpath("subdir", "file.txt")
        assert isinstance(result, PathType)

    def test_with_name_returns_pathtype(self):
        """with_name() returns PathType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.with_name("other.txt")
        assert isinstance(result, PathType)

    def test_with_stem_returns_pathtype(self):
        """with_stem() returns PathType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.with_stem("other")
        assert isinstance(result, PathType)

    def test_with_suffix_returns_pathtype(self):
        """with_suffix() returns PathType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.with_suffix(".md")
        assert isinstance(result, PathType)

    def test_resolve_returns_pathtype(self):
        """resolve() returns PathType."""
        pt = PathType.from_str("./file.txt")
        result = pt.resolve()
        assert isinstance(result, PathType)

    def test_absolute_returns_pathtype(self):
        """absolute() returns PathType."""
        pt = PathType.from_str("./file.txt")
        result = pt.absolute()
        assert isinstance(result, PathType)

    def test_relative_to_returns_pathtype(self):
        """relative_to() returns PathType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.relative_to("/home")
        assert isinstance(result, PathType)


# =============================================================================
# PATHTYPE TEST METHOD TESTS
# =============================================================================


class TestPathTypeTests:
    """PathType path test method tests."""

    def test_is_absolute_returns_booltype(self):
        """is_absolute() returns BoolType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.is_absolute()
        assert isinstance(result, BoolType)

    def test_is_relative_to_returns_booltype(self):
        """is_relative_to() returns BoolType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.is_relative_to("/home")
        assert isinstance(result, BoolType)

    def test_match_returns_booltype(self):
        """match() returns BoolType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.match("*.txt")
        assert isinstance(result, BoolType)


# =============================================================================
# PATHTYPE FILESYSTEM OPERATION TESTS
# =============================================================================


class TestPathTypeFilesystem:
    """PathType filesystem operation tests."""

    def test_exists_returns_booltype(self):
        """exists() returns BoolType."""
        pt = PathType.from_str("/tmp")
        result = pt.exists()
        assert isinstance(result, BoolType)

    def test_is_file_returns_booltype(self):
        """is_file() returns BoolType."""
        pt = PathType.from_str("/tmp")
        result = pt.is_file()
        assert isinstance(result, BoolType)

    def test_is_dir_returns_booltype(self):
        """is_dir() returns BoolType."""
        pt = PathType.from_str("/tmp")
        result = pt.is_dir()
        assert isinstance(result, BoolType)

    def test_is_symlink_returns_booltype(self):
        """is_symlink() returns BoolType."""
        pt = PathType.from_str("/tmp")
        result = pt.is_symlink()
        assert isinstance(result, BoolType)

    def test_is_mount_returns_booltype(self):
        """is_mount() returns BoolType."""
        pt = PathType.from_str("/")
        result = pt.is_mount()
        assert isinstance(result, BoolType)


# =============================================================================
# PATHTYPE CONVERSION TESTS
# =============================================================================


class TestPathTypeConversions:
    """PathType conversion tests."""

    def test_as_posix_returns_strtype(self):
        """as_posix() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.as_posix()
        assert isinstance(result, StrType)

    def test_as_uri_returns_strtype(self):
        """as_uri() returns StrType."""
        pt = PathType.from_str("/home/user/file.txt")
        result = pt.as_uri()
        assert isinstance(result, StrType)
