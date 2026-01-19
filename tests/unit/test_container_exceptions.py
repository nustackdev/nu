"""Tests for container exception hierarchy."""

import pytest

from everykv._exception import EveryShapeError
from everykv.container.exceptions import (
    ContainerCollisionError,
    ContainerError,
    ContainerExistsError,
    ContainerInvalidDepthError,
    ContainerInvalidSiteError,
    ContainerNotFoundError,
    ContainerParentMalformedError,
    ContainerParentNotFoundError,
    ContainerTypeError,
)


class TestContainerErrorBase:
    """Test base ContainerError exception."""

    def test_container_error_can_be_raised(self):
        """Test that ContainerError can be raised."""
        with pytest.raises(ContainerError):
            raise ContainerError()

    def test_container_error_can_be_caught(self):
        """Test that ContainerError can be caught."""
        try:
            raise ContainerError("test error")
        except ContainerError:
            pass
        else:
            pytest.fail("ContainerError was not caught")

    def test_container_error_message_handling(self):
        """Test that ContainerError message is stored correctly."""
        message = "Container operation failed"
        exc = ContainerError(message)
        assert str(exc) == message

    def test_container_error_inherits_from_everyshape_error(self):
        """Test that ContainerError inherits from EveryShapeError."""
        exc = ContainerError("test")
        assert isinstance(exc, EveryShapeError)
        assert isinstance(exc, Exception)
        assert issubclass(ContainerError, EveryShapeError)


class TestContainerNotFoundError:
    """Test ContainerNotFoundError exception."""

    def test_container_not_found_error_can_be_raised(self):
        """Test that ContainerNotFoundError can be raised."""
        with pytest.raises(ContainerNotFoundError):
            raise ContainerNotFoundError()

    def test_container_not_found_error_can_be_caught(self):
        """Test that ContainerNotFoundError can be caught."""
        try:
            raise ContainerNotFoundError("site not found")
        except ContainerNotFoundError:
            pass
        else:
            pytest.fail("ContainerNotFoundError was not caught")

    def test_container_not_found_error_caught_as_container_error(self):
        """Test that ContainerNotFoundError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerNotFoundError("site missing")

    def test_container_not_found_error_message(self):
        """Test ContainerNotFoundError message handling."""
        message = "Site does not exist in storage"
        exc = ContainerNotFoundError(message)
        assert str(exc) == message

    def test_container_not_found_error_inheritance(self):
        """Test ContainerNotFoundError inheritance chain."""
        exc = ContainerNotFoundError("test")
        assert isinstance(exc, ContainerNotFoundError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ContainerNotFoundError, ContainerError)


class TestContainerExistsError:
    """Test ContainerExistsError exception."""

    def test_container_exists_error_can_be_raised(self):
        """Test that ContainerExistsError can be raised."""
        with pytest.raises(ContainerExistsError):
            raise ContainerExistsError()

    def test_container_exists_error_can_be_caught(self):
        """Test that ContainerExistsError can be caught."""
        try:
            raise ContainerExistsError("site already exists")
        except ContainerExistsError:
            pass
        else:
            pytest.fail("ContainerExistsError was not caught")

    def test_container_exists_error_caught_as_container_error(self):
        """Test that ContainerExistsError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerExistsError("site exists")

    def test_container_exists_error_message(self):
        """Test ContainerExistsError message handling."""
        message = "Site already exists in storage"
        exc = ContainerExistsError(message)
        assert str(exc) == message

    def test_container_exists_error_inheritance(self):
        """Test ContainerExistsError inheritance chain."""
        exc = ContainerExistsError("test")
        assert isinstance(exc, ContainerExistsError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ContainerExistsError, ContainerError)


class TestContainerInvalidSiteError:
    """Test ContainerInvalidSiteError exception."""

    def test_invalid_site_error_can_be_raised(self):
        """Test that ContainerInvalidSiteError can be raised."""
        with pytest.raises(ContainerInvalidSiteError):
            raise ContainerInvalidSiteError()

    def test_invalid_site_error_can_be_caught(self):
        """Test that ContainerInvalidSiteError can be caught."""
        try:
            raise ContainerInvalidSiteError("invalid site")
        except ContainerInvalidSiteError:
            pass
        else:
            pytest.fail("ContainerInvalidSiteError was not caught")

    def test_invalid_site_error_caught_as_container_error(self):
        """Test that ContainerInvalidSiteError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerInvalidSiteError("empty tuple site")

    def test_invalid_site_error_message(self):
        """Test ContainerInvalidSiteError message handling."""
        message = "Site is empty tuple or has wrong root"
        exc = ContainerInvalidSiteError(message)
        assert str(exc) == message

    def test_invalid_site_error_inheritance(self):
        """Test ContainerInvalidSiteError inheritance chain."""
        exc = ContainerInvalidSiteError("test")
        assert isinstance(exc, ContainerInvalidSiteError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ContainerInvalidSiteError, ContainerError)


class TestContainerTypeError:
    """Test ContainerTypeError exception."""

    def test_container_type_error_can_be_raised(self):
        """Test that ContainerTypeError can be raised."""
        with pytest.raises(ContainerTypeError):
            raise ContainerTypeError()

    def test_container_type_error_can_be_caught(self):
        """Test that ContainerTypeError can be caught."""
        try:
            raise ContainerTypeError("type mismatch")
        except ContainerTypeError:
            pass
        else:
            pytest.fail("ContainerTypeError was not caught")

    def test_container_type_error_caught_as_container_error(self):
        """Test that ContainerTypeError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerTypeError("malformed data")

    def test_container_type_error_message(self):
        """Test ContainerTypeError message handling."""
        message = "Type mismatch at site"
        exc = ContainerTypeError(message)
        assert str(exc) == message

    def test_container_type_error_inheritance(self):
        """Test ContainerTypeError inheritance chain."""
        exc = ContainerTypeError("test")
        assert isinstance(exc, ContainerTypeError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ContainerTypeError, ContainerError)


class TestContainerCollisionError:
    """Test ContainerCollisionError exception."""

    def test_container_collision_error_can_be_raised(self):
        """Test that ContainerCollisionError can be raised."""
        with pytest.raises(ContainerCollisionError):
            raise ContainerCollisionError()

    def test_container_collision_error_can_be_caught(self):
        """Test that ContainerCollisionError can be caught."""
        try:
            raise ContainerCollisionError("collision detected")
        except ContainerCollisionError:
            pass
        else:
            pytest.fail("ContainerCollisionError was not caught")

    def test_container_collision_error_caught_as_container_type_error(self):
        """Test that ContainerCollisionError can be caught as ContainerTypeError."""
        with pytest.raises(ContainerTypeError):
            raise ContainerCollisionError("primitive collision")

    def test_container_collision_error_caught_as_container_error(self):
        """Test that ContainerCollisionError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerCollisionError("collision")

    def test_container_collision_error_message(self):
        """Test ContainerCollisionError message handling."""
        message = "Primitive value collides with container site"
        exc = ContainerCollisionError(message)
        assert str(exc) == message

    def test_container_collision_error_inheritance_from_container_type_error(self):
        """Test ContainerCollisionError inherits from ContainerTypeError."""
        exc = ContainerCollisionError("test")
        assert isinstance(exc, ContainerCollisionError)
        assert isinstance(exc, ContainerTypeError)
        assert issubclass(ContainerCollisionError, ContainerTypeError)

    def test_container_collision_error_full_inheritance_chain(self):
        """Test ContainerCollisionError full inheritance chain."""
        exc = ContainerCollisionError("test")
        assert isinstance(exc, ContainerCollisionError)
        assert isinstance(exc, ContainerTypeError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)


class TestContainerParentNotFoundError:
    """Test ContainerParentNotFoundError exception."""

    def test_parent_not_found_error_can_be_raised(self):
        """Test that ContainerParentNotFoundError can be raised."""
        with pytest.raises(ContainerParentNotFoundError):
            raise ContainerParentNotFoundError()

    def test_parent_not_found_error_can_be_caught(self):
        """Test that ContainerParentNotFoundError can be caught."""
        try:
            raise ContainerParentNotFoundError("parent missing")
        except ContainerParentNotFoundError:
            pass
        else:
            pytest.fail("ContainerParentNotFoundError was not caught")

    def test_parent_not_found_error_caught_as_container_not_found_error(self):
        """Test that ContainerParentNotFoundError can be caught as ContainerNotFoundError."""
        with pytest.raises(ContainerNotFoundError):
            raise ContainerParentNotFoundError("parent not found")

    def test_parent_not_found_error_caught_as_container_error(self):
        """Test that ContainerParentNotFoundError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerParentNotFoundError("no parent")

    def test_parent_not_found_error_message(self):
        """Test ContainerParentNotFoundError message handling."""
        message = "Parent site is missing from storage"
        exc = ContainerParentNotFoundError(message)
        assert str(exc) == message

    def test_parent_not_found_error_inheritance_from_container_not_found_error(self):
        """Test ContainerParentNotFoundError inherits from ContainerNotFoundError."""
        exc = ContainerParentNotFoundError("test")
        assert isinstance(exc, ContainerParentNotFoundError)
        assert isinstance(exc, ContainerNotFoundError)
        assert issubclass(ContainerParentNotFoundError, ContainerNotFoundError)

    def test_parent_not_found_error_full_inheritance_chain(self):
        """Test ContainerParentNotFoundError full inheritance chain."""
        exc = ContainerParentNotFoundError("test")
        assert isinstance(exc, ContainerParentNotFoundError)
        assert isinstance(exc, ContainerNotFoundError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)


class TestContainerParentMalformedError:
    """Test ContainerParentMalformedError exception."""

    def test_parent_malformed_error_can_be_raised(self):
        """Test that ContainerParentMalformedError can be raised."""
        with pytest.raises(ContainerParentMalformedError):
            raise ContainerParentMalformedError()

    def test_parent_malformed_error_can_be_caught(self):
        """Test that ContainerParentMalformedError can be caught."""
        try:
            raise ContainerParentMalformedError("parent corrupted")
        except ContainerParentMalformedError:
            pass
        else:
            pytest.fail("ContainerParentMalformedError was not caught")

    def test_parent_malformed_error_caught_as_container_type_error(self):
        """Test that ContainerParentMalformedError can be caught as ContainerTypeError."""
        with pytest.raises(ContainerTypeError):
            raise ContainerParentMalformedError("parent malformed")

    def test_parent_malformed_error_caught_as_container_error(self):
        """Test that ContainerParentMalformedError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerParentMalformedError("corrupted")

    def test_parent_malformed_error_message(self):
        """Test ContainerParentMalformedError message handling."""
        message = "Parent has corrupted or invalid data"
        exc = ContainerParentMalformedError(message)
        assert str(exc) == message

    def test_parent_malformed_error_inheritance_from_container_type_error(self):
        """Test ContainerParentMalformedError inherits from ContainerTypeError."""
        exc = ContainerParentMalformedError("test")
        assert isinstance(exc, ContainerParentMalformedError)
        assert isinstance(exc, ContainerTypeError)
        assert issubclass(ContainerParentMalformedError, ContainerTypeError)

    def test_parent_malformed_error_full_inheritance_chain(self):
        """Test ContainerParentMalformedError full inheritance chain."""
        exc = ContainerParentMalformedError("test")
        assert isinstance(exc, ContainerParentMalformedError)
        assert isinstance(exc, ContainerTypeError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)


class TestContainerInvalidDepthError:
    """Test ContainerInvalidDepthError exception."""

    def test_invalid_depth_error_can_be_raised(self):
        """Test that ContainerInvalidDepthError can be raised."""
        with pytest.raises(ContainerInvalidDepthError):
            raise ContainerInvalidDepthError()

    def test_invalid_depth_error_can_be_caught(self):
        """Test that ContainerInvalidDepthError can be caught."""
        try:
            raise ContainerInvalidDepthError("negative depth")
        except ContainerInvalidDepthError:
            pass
        else:
            pytest.fail("ContainerInvalidDepthError was not caught")

    def test_invalid_depth_error_caught_as_container_error(self):
        """Test that ContainerInvalidDepthError can be caught as ContainerError."""
        with pytest.raises(ContainerError):
            raise ContainerInvalidDepthError("invalid depth")

    def test_invalid_depth_error_message(self):
        """Test ContainerInvalidDepthError message handling."""
        message = "Invalid depth parameter provided"
        exc = ContainerInvalidDepthError(message)
        assert str(exc) == message

    def test_invalid_depth_error_inheritance(self):
        """Test ContainerInvalidDepthError inheritance chain."""
        exc = ContainerInvalidDepthError("test")
        assert isinstance(exc, ContainerInvalidDepthError)
        assert isinstance(exc, ContainerError)
        assert isinstance(exc, EveryShapeError)
        assert issubclass(ContainerInvalidDepthError, ContainerError)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_container_error(self):
        """Test that all container exceptions inherit from ContainerError."""
        exceptions = [
            ContainerNotFoundError,
            ContainerExistsError,
            ContainerInvalidSiteError,
            ContainerTypeError,
            ContainerCollisionError,
            ContainerParentNotFoundError,
            ContainerParentMalformedError,
            ContainerInvalidDepthError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, ContainerError), (
                f"{exc_class.__name__} should inherit from ContainerError"
            )

    def test_all_exceptions_inherit_from_everyshape_error(self):
        """Test that all container exceptions inherit from EveryShapeError."""
        exceptions = [
            ContainerError,
            ContainerNotFoundError,
            ContainerExistsError,
            ContainerInvalidSiteError,
            ContainerTypeError,
            ContainerCollisionError,
            ContainerParentNotFoundError,
            ContainerParentMalformedError,
            ContainerInvalidDepthError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, EveryShapeError), (
                f"{exc_class.__name__} should inherit from EveryShapeError"
            )

    def test_container_collision_error_hierarchy(self):
        """Test ContainerCollisionError inherits from ContainerTypeError."""
        assert issubclass(ContainerCollisionError, ContainerTypeError)
        assert issubclass(ContainerCollisionError, ContainerError)

    def test_parent_not_found_error_hierarchy(self):
        """Test ContainerParentNotFoundError inherits from ContainerNotFoundError."""
        assert issubclass(ContainerParentNotFoundError, ContainerNotFoundError)
        assert issubclass(ContainerParentNotFoundError, ContainerError)

    def test_parent_malformed_error_hierarchy(self):
        """Test ContainerParentMalformedError inherits from ContainerTypeError."""
        assert issubclass(ContainerParentMalformedError, ContainerTypeError)
        assert issubclass(ContainerParentMalformedError, ContainerError)
