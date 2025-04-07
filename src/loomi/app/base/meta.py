from abc import ABCMeta
from inspect import Parameter, Signature
from types import FunctionType, MethodType
from typing import Any, ClassVar, Optional, Type, TypedDict, TypeVar, cast, overload

from loomi.app.handlers.composer import AppDescriptor
from loomi.app.handlers.services import ServiceDescriptor

# Updated imports for Python 3.10+ style
# Using regular dict, list instead of Dict, List


T = TypeVar("T")


# Unified TypedDict for storing both spec and nested app information
class ComponentInfo(TypedDict):
    type: Type[Any]
    type_name: str
    param_name: str
    is_app: bool  # True for apps, False for services


class AppMeta(ABCMeta):
    """
    Metaclass for App classes that handles service initialization and nested apps.

    This metaclass enhances IDE support by:
    1. Identifying class attributes that are services (instances of ServiceDescriptor)
    2. Identifying class attributes that are nested apps (instances of AppDescriptor)
    3. Generating an __init__ method with proper type annotations for each service spec and nested app

    Example:
        ```python
        class NestedApp(AsyncApp):
            database = UseService(DB)

        class MyApp(AsyncApp):
            database = UseService(DB)
            auth = UseService(Auth)
            sub_app = UseApp(NestedApp)

        # IDE will show proper hints for these parameters:
        app = MyApp(
            database_spec=CustomDatabaseSpec(),
            auth_spec=CustomAuthSpec(),
            sub_app={
                "database_spec": NestedDBSpec()
            }
        )
        ```
    """

    @overload
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> Type[T]: ...  # type: ignore

    @overload
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> Type[T]: ...  # type: ignore

    def __new__(  # noqa: C901
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> Type[T]:  # type: ignore
        """
        Create a new App class with enhanced IDE support for services and nested apps.

        Args:
            name: The name of the class being created
            bases: The base classes of the class being created
            namespace: The namespace (attributes and methods) of the class being created
            **kwargs: Additional keyword arguments passed to the metaclass

        Returns:
            A new class with enhanced IDE support
        """
        # Find all ServiceDescriptor instances in the namespace
        services: dict[str, ServiceDescriptor] = {
            attr_name: attr_value
            for attr_name, attr_value in namespace.items()
            if isinstance(attr_value, ServiceDescriptor)
        }

        # Find all AppDescriptor instances in the namespace
        nested_apps: dict[str, AppDescriptor] = {
            attr_name: attr_value
            for attr_name, attr_value in namespace.items()
            if isinstance(attr_value, AppDescriptor)
        }

        # Store the original __init__ if it exists
        original_init: Optional[FunctionType] = namespace.get("__init__")
        original_annotations: dict[str, Any] = namespace.get("__annotations__", {}).copy()

        # Create unified component info for both services and nested apps
        component_info: dict[str, ComponentInfo] = {}
        init_annotations: dict[str, Any] = {}

        # Process service specs
        for service_name, service_descriptor in services.items():
            spec_param_name = f"{service_name}_spec"

            # Determine the correct type annotation
            spec_type: Type[Any]
            if isinstance(service_descriptor.spec, type):
                spec_type = service_descriptor.spec
            else:
                spec_type = type(service_descriptor.spec)

            spec_type_name = spec_type.__name__

            component_info[service_name] = {
                "type": spec_type,
                "type_name": spec_type_name,
                "param_name": spec_param_name,
                "is_app": False,
            }

            init_annotations[spec_param_name] = Optional[spec_type]

        # Process nested apps
        for app_name, app_descriptor in nested_apps.items():
            app_param_name = app_name
            app_class = app_descriptor.app
            app_type_name = app_class.__name__

            component_info[app_name] = {
                "type": app_class,
                "type_name": app_type_name,
                "param_name": app_param_name,
                "is_app": True,
            }

            # Use dict for nested app configurations
            init_annotations[app_param_name] = Optional[dict[str, Any]]

        # Store annotations in the namespace
        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}
        namespace["__annotations__"].update(original_annotations)

        # Helper function to call parent __init__
        def _call_parent_init(instance: Any, args: tuple, kwargs: dict) -> None:
            """Helper function to call the first non-AppMeta parent's __init__"""
            for base in instance.__class__.__mro__[1:]:  # Skip self.__class__
                if base is object:
                    continue  # Skip object.__init__

                # Skip AppMeta-based classes to avoid recursion
                if isinstance(base, AppMeta):
                    continue

                # Call the first non-AppMeta base class's __init__
                if hasattr(base, "__init__"):
                    base.__init__(instance, *args, **kwargs)
                    break

        # Generate a properly typed __init__ method
        def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
            """
            Initialize the App instance with optional service specifications and nested apps.
            """
            # Initialize the specs dictionary
            self._specs: dict[str, object] = {}  # type: ignore

            # Initialize the nested apps dictionary
            self._app_deps_specs: dict[str, object] = {}  # type: ignore

            # Process spec parameters
            for service_name in self.__class__._service_descriptors:
                spec_param_name = f"{service_name}_spec"
                if spec_param_name in kwargs:
                    self._specs[service_name] = kwargs.pop(spec_param_name)

            # Process nested app parameters
            for app_name, app_descriptor in self.__class__._app_descriptors.items():
                if app_name in kwargs:
                    app_config = kwargs.pop(app_name)

                    # Create an instance of the nested app with the provided configuration
                    if app_config is not None:
                        # Handle both dict and instance inputs
                        if isinstance(app_config, dict):
                            # Create new instance with config passed as kwargs
                            self._app_deps_specs[app_name] = app_config
                        else:
                            # TODO: Raise an error if the instance is not of the correct type
                            pass

            # Call original __init__ if it exists
            if original_init:
                original_init(self, *args, **kwargs)
            else:
                # Find and call the appropriate parent __init__
                _call_parent_init(self, args, kwargs)

        # Add the generated methods to the namespace
        namespace["__init__"] = __init__

        # Store descriptors on the class as class variables with proper typing
        namespace["_service_descriptors"] = services
        namespace["_app_descriptors"] = nested_apps

        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}

        namespace["__annotations__"]["_service_descriptors"] = ClassVar[
            dict[str, ServiceDescriptor]
        ]
        namespace["__annotations__"]["_app_descriptors"] = ClassVar[dict[str, AppDescriptor]]

        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        # Generate parameter documentation
        param_docs: list[str] = []

        # Add documentation for all components (both services and apps)
        for component_name, info in component_info.items():
            if info["is_app"]:
                param_docs.append(
                    f"\t{info['param_name']} (Optional[dict[str, Any]]): "
                    f"Configuration dictionary for the {component_name} nested app. "
                    f"Keys should match parameter names for {info['type_name']}."
                )
            else:
                param_docs.append(
                    f"\t{info['param_name']} (Optional[{info['type_name']}]): "
                    f"Specification for the {component_name} service. "
                    f"Overrides the default specification if provided."
                )

        # Update the docstring with parameter documentation
        if param_docs:
            init_method = cast(MethodType, cls.__init__)
            existing_doc = init_method.__doc__ or ""

            # Format the docstring properly
            if "Args:" in existing_doc:
                # Insert our parameters before the closing section
                parts = existing_doc.split("Args:")
                updated_doc = (
                    f"{parts[0]}Args:\n{''.join(param_docs)}\n"
                    f"\t*args: Positional arguments passed to parent initializers.\n"
                    f"\t**kwargs: Additional keyword arguments."
                )
            else:
                # Add our parameters section
                if existing_doc and not existing_doc.strip().endswith("\n"):
                    existing_doc += "\n\n"
                else:
                    existing_doc += "\n" if existing_doc else ""
                updated_doc = (
                    existing_doc
                    + "Args:\n"
                    + "\n".join(param_docs)
                    + "\n\t*args: Positional arguments passed to parent initializers.\n"
                    + "\t**kwargs: Additional keyword arguments."
                )

            init_method.__doc__ = updated_doc

        # Create a proper __signature__ for IDE inspection
        parameters = [
            Parameter(name="self", kind=Parameter.POSITIONAL_OR_KEYWORD, annotation=cls),
            Parameter(name="args", kind=Parameter.VAR_POSITIONAL, annotation=Any),
        ]

        # Add parameters for all components
        for component_name, info in component_info.items():
            if info["is_app"]:
                parameters.append(
                    Parameter(
                        name=info["param_name"],
                        kind=Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=Optional[dict[str, Any]],
                    )
                )
            else:
                parameters.append(
                    Parameter(
                        name=info["param_name"],
                        kind=Parameter.KEYWORD_ONLY,
                        default=None,
                        annotation=Optional[info["type"]],
                    )
                )

        # Add **kwargs parameter
        parameters.append(Parameter(name="kwargs", kind=Parameter.VAR_KEYWORD, annotation=Any))

        # Set signature on __init__ method
        init_signature = Signature(parameters=parameters, return_annotation=None)
        cls.__init__.__signature__ = init_signature  # type: ignore

        # Add __init__ annotations to help IDE completion
        setattr(cls, "__init__.__annotations__", init_annotations)

        # Set the return type hint for __new__ to help IDE show correct type for constructors
        setattr(cls, "__new__.__annotations__", {"return": cls})

        return cast(Type[T], cls)
