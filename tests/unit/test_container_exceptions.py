"""Tests for container exception hierarchy."""

import pytest

from everyshape._exception import EveryShapeError
from everyshape.container.exceptions import (
    InvalidDepthError,
    InvalidPathError,
    ParentMalformedError,
    ParentNotFoundError,
    PathCollisionError,
    PathExistsError,
    PathNotFoundError,
    PathTypeError,
    TreeError,
)


class TestTreeErrorBase:
    """Test base TreeError exception."""

    def test_tree_error_can_be_raised(self):
        """Test that TreeError can be raised."""
        with pytest.raises(TreeError):
            raise TreeError()

    def test_tree_error_can_be_caught(self):
        """Test that TreeError can be caught."""
        try:
            raise TreeError("test error")
        except TreeError:
            pass
        else:
            pytest.fail("TreeError was not caught")

    def test_tree_error_message_handling(self):
        """Test that TreeError message is stored correctly."""
        message = "Tree operation failed"
        exc = TreeError(message)
        assert str(exc) == message

    def test_tree_error_inherits_from_everyshape_error(self):
        """Test that TreeError inherits from EveryShapeError."""
        exc = TreeError("test")
        assert isinstance(exc, EveryShapeError)
        assert isinstance(exc, Exception)
        assert issubclass(TreeError, EveryShapeError)


class TestPathNotFoundError:
    """Test PathNotFoundError exception."""

    def test_path_not_found_error_can_be_raised(self):
        """Test that PathNotFoundError can be raised."""
        with pytest.raises(PathNotFoundError):
            raise PathNotFoundError()

    def test_path_not_found_error_can_be_caught(self):
        """Test that PathNotFoundError can be caught."""
        try:
            raise PathNotFoundError("path not found")
        except PathNotFoundError:
            pass
        else:
            pytest.fail("PathNotFoundError was not caught")

    def test_path_not_found_error_caught_as_tree_error(self):
        """Test that PathNotFoundError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise PathNotFoundError("path missing")

    def test_path_not_found_error_message(self):
        """Test PathNotFoundError message handling."""
        message = "Path does not exist in storage"
        exc = PathNotFoundError(message)
        assert str(exc) == message

    def test_path_not_found_error_inheritance(self):
        """Test PathNotFoundError inheritance chain."""
        exc = PathNotFoundError("test")
        assert isinstance(exc, PathNotFoundError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(PathNotFoundError, TreeError)


class TestPathExistsError:
    """Test PathExistsError exception."""

    def test_path_exists_error_can_be_raised(self):
        """Test that PathExistsError can be raised."""
        with pytest.raises(PathExistsError):
            raise PathExistsError()

    def test_path_exists_error_can_be_caught(self):
        """Test that PathExistsError can be caught."""
        try:
            raise PathExistsError("path already exists")
        except PathExistsError:
            pass
        else:
            pytest.fail("PathExistsError was not caught")

    def test_path_exists_error_caught_as_tree_error(self):
        """Test that PathExistsError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise PathExistsError("path exists")

    def test_path_exists_error_message(self):
        """Test PathExistsError message handling."""
        message = "Path already exists in storage"
        exc = PathExistsError(message)
        assert str(exc) == message

    def test_path_exists_error_inheritance(self):
        """Test PathExistsError inheritance chain."""
        exc = PathExistsError("test")
        assert isinstance(exc, PathExistsError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(PathExistsError, TreeError)


class TestInvalidPathError:
    """Test InvalidPathError exception."""

    def test_invalid_path_error_can_be_raised(self):
        """Test that InvalidPathError can be raised."""
        with pytest.raises(InvalidPathError):
            raise InvalidPathError()

    def test_invalid_path_error_can_be_caught(self):
        """Test that InvalidPathError can be caught."""
        try:
            raise InvalidPathError("invalid path")
        except InvalidPathError:
            pass
        else:
            pytest.fail("InvalidPathError was not caught")

    def test_invalid_path_error_caught_as_tree_error(self):
        """Test that InvalidPathError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise InvalidPathError("empty tuple path")

    def test_invalid_path_error_message(self):
        """Test InvalidPathError message handling."""
        message = "Path is empty tuple or has wrong root"
        exc = InvalidPathError(message)
        assert str(exc) == message

    def test_invalid_path_error_inheritance(self):
        """Test InvalidPathError inheritance chain."""
        exc = InvalidPathError("test")
        assert isinstance(exc, InvalidPathError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(InvalidPathError, TreeError)


class TestPathTypeError:
    """Test PathTypeError exception."""

    def test_path_type_error_can_be_raised(self):
        """Test that PathTypeError can be raised."""
        with pytest.raises(PathTypeError):
            raise PathTypeError()

    def test_path_type_error_can_be_caught(self):
        """Test that PathTypeError can be caught."""
        try:
            raise PathTypeError("type mismatch")
        except PathTypeError:
            pass
        else:
            pytest.fail("PathTypeError was not caught")

    def test_path_type_error_caught_as_tree_error(self):
        """Test that PathTypeError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise PathTypeError("malformed data")

    def test_path_type_error_message(self):
        """Test PathTypeError message handling."""
        message = "Type mismatch at path"
        exc = PathTypeError(message)
        assert str(exc) == message

    def test_path_type_error_inheritance(self):
        """Test PathTypeError inheritance chain."""
        exc = PathTypeError("test")
        assert isinstance(exc, PathTypeError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(PathTypeError, TreeError)


class TestPathCollisionError:
    """Test PathCollisionError exception."""

    def test_path_collision_error_can_be_raised(self):
        """Test that PathCollisionError can be raised."""
        with pytest.raises(PathCollisionError):
            raise PathCollisionError()

    def test_path_collision_error_can_be_caught(self):
        """Test that PathCollisionError can be caught."""
        try:
            raise PathCollisionError("collision detected")
        except PathCollisionError:
            pass
        else:
            pytest.fail("PathCollisionError was not caught")

    def test_path_collision_error_caught_as_path_type_error(self):
        """Test that PathCollisionError can be caught as PathTypeError."""
        with pytest.raises(PathTypeError):
            raise PathCollisionError("primitive collision")

    def test_path_collision_error_caught_as_tree_error(self):
        """Test that PathCollisionError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise PathCollisionError("collision")

    def test_path_collision_error_message(self):
        """Test PathCollisionError message handling."""
        message = "Primitive value collides with container path"
        exc = PathCollisionError(message)
        assert str(exc) == message

    def test_path_collision_error_inheritance_from_path_type_error(self):
        """Test PathCollisionError inherits from PathTypeError."""
        exc = PathCollisionError("test")
        assert isinstance(exc, PathCollisionError)
        assert isinstance(exc, PathTypeError)
        assert issubclass(PathCollisionError, PathTypeError)

    def test_path_collision_error_full_inheritance_chain(self):
        """Test PathCollisionError full inheritance chain."""
        exc = PathCollisionError("test")
        assert isinstance(exc, PathCollisionError)
        assert isinstance(exc, PathTypeError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)


class TestParentNotFoundError:
    """Test ParentNotFoundError exception."""

    def test_parent_not_found_error_can_be_raised(self):
        """Test that ParentNotFoundError can be raised."""
        with pytest.raises(ParentNotFoundError):
            raise ParentNotFoundError()

    def test_parent_not_found_error_can_be_caught(self):
        """Test that ParentNotFoundError can be caught."""
        try:
            raise ParentNotFoundError("parent missing")
        except ParentNotFoundError:
            pass
        else:
            pytest.fail("ParentNotFoundError was not caught")

    def test_parent_not_found_error_caught_as_path_not_found_error(self):
        """Test that ParentNotFoundError can be caught as PathNotFoundError."""
        with pytest.raises(PathNotFoundError):
            raise ParentNotFoundError("parent not found")

    def test_parent_not_found_error_caught_as_tree_error(self):
        """Test that ParentNotFoundError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise ParentNotFoundError("no parent")

    def test_parent_not_found_error_message(self):
        """Test ParentNotFoundError message handling."""
        message = "Parent path is missing from storage"
        exc = ParentNotFoundError(message)
        assert str(exc) == message

    def test_parent_not_found_error_inheritance_from_path_not_found_error(self):
        """Test ParentNotFoundError inherits from PathNotFoundError."""
        exc = ParentNotFoundError("test")
        assert isinstance(exc, ParentNotFoundError)
        assert isinstance(exc, PathNotFoundError)
        assert issubclass(ParentNotFoundError, PathNotFoundError)

    def test_parent_not_found_error_full_inheritance_chain(self):
        """Test ParentNotFoundError full inheritance chain."""
        exc = ParentNotFoundError("test")
        assert isinstance(exc, ParentNotFoundError)
        assert isinstance(exc, PathNotFoundError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)


class TestParentMalformedError:
    """Test ParentMalformedError exception."""

    def test_parent_malformed_error_can_be_raised(self):
        """Test that ParentMalformedError can be raised."""
        with pytest.raises(ParentMalformedError):
            raise ParentMalformedError()

    def test_parent_malformed_error_can_be_caught(self):
        """Test that ParentMalformedError can be caught."""
        try:
            raise ParentMalformedError("parent corrupted")
        except ParentMalformedError:
            pass
        else:
            pytest.fail("ParentMalformedError was not caught")

    def test_parent_malformed_error_caught_as_path_type_error(self):
        """Test that ParentMalformedError can be caught as PathTypeError."""
        with pytest.raises(PathTypeError):
            raise ParentMalformedError("parent malformed")

    def test_parent_malformed_error_caught_as_tree_error(self):
        """Test that ParentMalformedError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise ParentMalformedError("corrupted")

    def test_parent_malformed_error_message(self):
        """Test ParentMalformedError message handling."""
        message = "Parent has corrupted or invalid data"
        exc = ParentMalformedError(message)
        assert str(exc) == message

    def test_parent_malformed_error_inheritance_from_path_type_error(self):
        """Test ParentMalformedError inherits from PathTypeError."""
        exc = ParentMalformedError("test")
        assert isinstance(exc, ParentMalformedError)
        assert isinstance(exc, PathTypeError)
        assert issubclass(ParentMalformedError, PathTypeError)

    def test_parent_malformed_error_full_inheritance_chain(self):
        """Test ParentMalformedError full inheritance chain."""
        exc = ParentMalformedError("test")
        assert isinstance(exc, ParentMalformedError)
        assert isinstance(exc, PathTypeError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)


class TestInvalidDepthError:
    """Test InvalidDepthError exception."""

    def test_invalid_depth_error_can_be_raised(self):
        """Test that InvalidDepthError can be raised."""
        with pytest.raises(InvalidDepthError):
            raise InvalidDepthError()

    def test_invalid_depth_error_can_be_caught(self):
        """Test that InvalidDepthError can be caught."""
        try:
            raise InvalidDepthError("negative depth")
        except InvalidDepthError:
            pass
        else:
            pytest.fail("InvalidDepthError was not caught")

    def test_invalid_depth_error_caught_as_tree_error(self):
        """Test that InvalidDepthError can be caught as TreeError."""
        with pytest.raises(TreeError):
            raise InvalidDepthError("invalid depth")

    def test_invalid_depth_error_message(self):
        """Test InvalidDepthError message handling."""
        message = "Invalid depth parameter provided"
        exc = InvalidDepthError(message)
        assert str(exc) == message

    def test_invalid_depth_error_inheritance(self):
        """Test InvalidDepthError inheritance chain."""
        exc = InvalidDepthError("test")
        assert isinstance(exc, InvalidDepthError)
        assert isinstance(exc, TreeError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(InvalidDepthError, TreeError)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_tree_error(self):
        """Test that all container exceptions inherit from TreeError."""
        exceptions = [
            PathNotFoundError,
            PathExistsError,
            InvalidPathError,
            PathTypeError,
            PathCollisionError,
            ParentNotFoundError,
            ParentMalformedError,
            InvalidDepthError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, TreeError), (
                f"{exc_class.__name__} should inherit from TreeError"
            )

    def test_all_exceptions_inherit_from_everyshape_error(self):
        """Test that all container exceptions inherit from EveryShapeError."""
        exceptions = [
            TreeError,
            PathNotFoundError,
            PathExistsError,
            InvalidPathError,
            PathTypeError,
            PathCollisionError,
            ParentNotFoundError,
            ParentMalformedError,
            InvalidDepthError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, EveryShapeError), (
                f"{exc_class.__name__} should inherit from EveryShapeError"
            )

    def test_path_collision_error_hierarchy(self):
        """Test PathCollisionError inherits from PathTypeError."""
        assert issubclass(PathCollisionError, PathTypeError)
        assert issubclass(PathCollisionError, TreeError)

    def test_parent_not_found_error_hierarchy(self):
        """Test ParentNotFoundError inherits from PathNotFoundError."""
        assert issubclass(ParentNotFoundError, PathNotFoundError)
        assert issubclass(ParentNotFoundError, TreeError)

    def test_parent_malformed_error_hierarchy(self):
        """Test ParentMalformedError inherits from PathTypeError."""
        assert issubclass(ParentMalformedError, PathTypeError)
        assert issubclass(ParentMalformedError, TreeError)

    def test_catch_collision_as_type_error(self):
        """Test catching PathCollisionError as PathTypeError."""
        with pytest.raises(PathTypeError):
            raise PathCollisionError("collision")

    def test_catch_parent_not_found_as_path_not_found(self):
        """Test catching ParentNotFoundError as PathNotFoundError."""
        with pytest.raises(PathNotFoundError):
            raise ParentNotFoundError("parent missing")

    def test_catch_parent_malformed_as_type_error(self):
        """Test catching ParentMalformedError as PathTypeError."""
        with pytest.raises(PathTypeError):
            raise ParentMalformedError("malformed")

    def test_exception_mro_path_collision_error(self):
        """Test Method Resolution Order for PathCollisionError."""
        mro = PathCollisionError.__mro__
        assert PathCollisionError in mro
        assert PathTypeError in mro
        assert TreeError in mro
        assert EveryShapeError in mro

    def test_exception_mro_parent_not_found_error(self):
        """Test Method Resolution Order for ParentNotFoundError."""
        mro = ParentNotFoundError.__mro__
        assert ParentNotFoundError in mro
        assert PathNotFoundError in mro
        assert TreeError in mro
        assert EveryShapeError in mro

    def test_exception_mro_parent_malformed_error(self):
        """Test Method Resolution Order for ParentMalformedError."""
        mro = ParentMalformedError.__mro__
        assert ParentMalformedError in mro
        assert PathTypeError in mro
        assert TreeError in mro
        assert EveryShapeError in mro

    def test_raise_and_catch_multiple_exception_types(self):
        """Test raising and catching various exception combinations."""
        # PathCollisionError can be caught as both PathCollisionError and PathTypeError
        with pytest.raises((PathCollisionError, PathTypeError)):
            raise PathCollisionError("collision detected")

        # ParentNotFoundError can be caught as both ParentNotFoundError and PathNotFoundError
        with pytest.raises((ParentNotFoundError, PathNotFoundError)):
            raise ParentNotFoundError("parent missing")

        # ParentMalformedError can be caught as both ParentMalformedError and PathTypeError
        with pytest.raises((ParentMalformedError, PathTypeError)):
            raise ParentMalformedError("malformed data")
