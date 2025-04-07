from __future__ import annotations

from typing import TYPE_CHECKING, cast

from loomi.app.base import App

from .descriptor import AppDescriptor
from .exceptions import DependencyError
from .logger import logger

if TYPE_CHECKING:
    pass

__all__ = [
    "AppCommonComposer",
]


class AppCommonComposer(App):
    def _initialize_app_composition_descriptors(self):
        apps_specs = getattr(self, "_app_deps_specs", {})

        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, AppDescriptor):
                continue

            app_descriptor = cast(AppDescriptor, value)
            app_factory = app_descriptor.app

            # Get the service spec:
            # First, check if app's service specs is passed as app __init__ argument
            app_spec = apps_specs.get(name, None)

            # If spec is not provided, try to use default spec from descriptor
            if app_spec is None:
                if app_descriptor.service_specs is not None:
                    app_spec = app_descriptor.service_specs

            # Raise an exception if spec is still not found
            if app_spec is None:
                logger.error(f"No spec found for app '{name}'")
                raise DependencyError(f"No spec found for app '{name}'")

            app = app_factory(**app_spec)
            self._app_deps[name] = app

            setattr(self, name, app)
