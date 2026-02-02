"""Unit tests for Path ref.

Tests for:
- PathRef (constructors, operations, methods)
"""

from every_path import PathValue as PathRef
from everybase import BoolValue as BoolRef
from everybase import DivOp, FuncCallOp
from everybase import ListValue as ListRef
from everybase import StrValue as StrRef
from everybase import TupleValue as TupleRef


# =============================================================================
# PATHREF CONSTRUCTION TESTS
# =============================================================================


class TestPathRefConstruction:
    """PathRef construction tests."""

    def test_from_str(self):
        """Create from string."""
        pt = PathRef.from_str("/home/user/file.txt")
        assert isinstance(pt, PathRef)
        assert isinstance(pt._source, FuncCallOp)

    def test_cwd(self):
        """Create from current working directory."""
        pt = PathRef.cwd()
        assert isinstance(pt, PathRef)

    def test_home(self):
        """Create from home directory."""
        pt = PathRef.home()
        assert isinstance(pt, PathRef)


# =============================================================================
# PATHREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestPathRefAccessors:
    """PathRef component accessor tests."""

    def test_name_returns_strref(self):
        """name() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.name()
        assert isinstance(result, StrRef)

    def test_stem_returns_strref(self):
        """stem() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.stem()
        assert isinstance(result, StrRef)

    def test_suffix_returns_strref(self):
        """suffix() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.suffix()
        assert isinstance(result, StrRef)

    def test_suffixes_returns_listref(self):
        """suffixes() returns ListRef."""
        pt = PathRef.from_str("/home/user/file.tar.gz")
        result = pt.suffixes()
        assert isinstance(result, ListRef)

    def test_parent_returns_pathref(self):
        """parent() returns PathRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.parent()
        assert isinstance(result, PathRef)

    def test_parents_returns_tupleref(self):
        """parents() returns TupleRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.parents()
        assert isinstance(result, TupleRef)

    def test_root_returns_strref(self):
        """root() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.root()
        assert isinstance(result, StrRef)

    def test_anchor_returns_strref(self):
        """anchor() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.anchor()
        assert isinstance(result, StrRef)

    def test_parts_returns_tupleref(self):
        """parts() returns TupleRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.parts()
        assert isinstance(result, TupleRef)


# =============================================================================
# PATHREF MANIPULATION TESTS
# =============================================================================


class TestPathRefManipulation:
    """PathRef manipulation tests."""

    def test_truediv_returns_pathref(self):
        """/ operator returns PathRef."""
        pt = PathRef.from_str("/home/user")
        result = pt / "subdir"
        assert isinstance(result, PathRef)
        assert isinstance(result._source, DivOp)

    def test_joinpath_returns_pathref(self):
        """joinpath() returns PathRef."""
        pt = PathRef.from_str("/home/user")
        result = pt.joinpath("subdir", "file.txt")
        assert isinstance(result, PathRef)

    def test_with_name_returns_pathref(self):
        """with_name() returns PathRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.with_name("other.txt")
        assert isinstance(result, PathRef)

    def test_with_stem_returns_pathref(self):
        """with_stem() returns PathRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.with_stem("other")
        assert isinstance(result, PathRef)

    def test_with_suffix_returns_pathref(self):
        """with_suffix() returns PathRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.with_suffix(".md")
        assert isinstance(result, PathRef)

    def test_resolve_path_returns_pathref(self):
        """resolve_path() returns PathRef."""
        pt = PathRef.from_str("./file.txt")
        result = pt.resolve_path()
        assert isinstance(result, PathRef)

    def test_absolute_returns_pathref(self):
        """absolute() returns PathRef."""
        pt = PathRef.from_str("./file.txt")
        result = pt.absolute()
        assert isinstance(result, PathRef)

    def test_relative_to_returns_pathref(self):
        """relative_to() returns PathRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.relative_to("/home")
        assert isinstance(result, PathRef)


# =============================================================================
# PATHREF TEST METHOD TESTS
# =============================================================================


class TestPathRefTests:
    """PathRef path test method tests."""

    def test_is_absolute_returns_boolref(self):
        """is_absolute() returns BoolRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.is_absolute()
        assert isinstance(result, BoolRef)

    def test_is_relative_to_returns_boolref(self):
        """is_relative_to() returns BoolRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.is_relative_to("/home")
        assert isinstance(result, BoolRef)

    def test_match_returns_boolref(self):
        """match() returns BoolRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.match("*.txt")
        assert isinstance(result, BoolRef)


# =============================================================================
# PATHREF FILESYSTEM OPERATION TESTS
# =============================================================================


class TestPathRefFilesystem:
    """PathRef filesystem operation tests."""

    def test_exists_returns_boolref(self):
        """exists() returns BoolRef."""
        pt = PathRef.from_str("/tmp")
        result = pt.exists()
        assert isinstance(result, BoolRef)

    def test_is_file_returns_boolref(self):
        """is_file() returns BoolRef."""
        pt = PathRef.from_str("/tmp")
        result = pt.is_file()
        assert isinstance(result, BoolRef)

    def test_is_dir_returns_boolref(self):
        """is_dir() returns BoolRef."""
        pt = PathRef.from_str("/tmp")
        result = pt.is_dir()
        assert isinstance(result, BoolRef)

    def test_is_symlink_returns_boolref(self):
        """is_symlink() returns BoolRef."""
        pt = PathRef.from_str("/tmp")
        result = pt.is_symlink()
        assert isinstance(result, BoolRef)

    def test_is_mount_returns_boolref(self):
        """is_mount() returns BoolRef."""
        pt = PathRef.from_str("/")
        result = pt.is_mount()
        assert isinstance(result, BoolRef)


# =============================================================================
# PATHREF CONVERSION TESTS
# =============================================================================


class TestPathRefConversions:
    """PathRef conversion tests."""

    def test_as_posix_returns_strref(self):
        """as_posix() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.as_posix()
        assert isinstance(result, StrRef)

    def test_as_uri_returns_strref(self):
        """as_uri() returns StrRef."""
        pt = PathRef.from_str("/home/user/file.txt")
        result = pt.as_uri()
        assert isinstance(result, StrRef)
