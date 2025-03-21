from abc import ABCMeta
from inspect import Parameter, Signature
from types import FunctionType, MethodType
from typing import Any, ClassVar, Dict, List, Optional, Type, TypedDict, TypeVar, cast, overload

from loomi.app.handlers.services import ServiceDescriptor

T = TypeVar("T")


# TypedDict for storing spec information
class SpecInfo(TypedDict):
    type: Type[Any]
    type_name: str
    param_name: str


class AppMeta(ABCMeta):
    """
    Metaclass for App classes that handles service initialization.

    This metaclass enhances IDE support by:
    1. Identifying class attributes that are services (instances of ServiceDescriptor)
    2. Generating an __init__ method with proper type annotations for each service spec

    Example:
        ```python
        class MyApp(AsyncApp):
            database = UseService(DB)
            auth = UseService(Auth)

        # IDE will show proper hints for these parameters:
        app = MyApp(database_spec=CustomDatabaseSpec(), auth_spec=CustomAuthSpec())
        ```
    """

    @overload
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: Dict[str, Any],
    ) -> Type[T]: ...  # type: ignore

    @overload
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> Type[T]: ...  # type: ignore

    def __new__(  # noqa: C901
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> Type[T]:  # type: ignore
        """
        Create a new App class with enhanced IDE support.

        Args:
            name: The name of the class being created
            bases: The base classes of the class being created
            namespace: The namespace (attributes and methods) of the class being created
            **kwargs: Additional keyword arguments passed to the metaclass

        Returns:
            A new class with enhanced IDE support
        """
        # Find all ServiceDescriptor instances in the namespace
        services: Dict[str, ServiceDescriptor] = {
            attr_name: attr_value
            for attr_name, attr_value in namespace.items()
            if isinstance(attr_value, ServiceDescriptor)
        }

        # Store the original __init__ if it exists
        original_init: Optional[FunctionType] = namespace.get("__init__")
        original_annotations: Dict[str, Any] = namespace.get("__annotations__", {}).copy()

        # Extract spec information for each service
        spec_info: Dict[str, SpecInfo] = {}
        init_annotations: Dict[str, Any] = {}

        for service_name, service_descriptor in services.items():
            spec_param_name = f"{service_name}_spec"

            # Determine the correct type annotation
            spec_type: Type[Any]
            if isinstance(service_descriptor.spec, type):
                spec_type = service_descriptor.spec
            else:
                spec_type = type(service_descriptor.spec)

            spec_type_name = spec_type.__name__

            spec_info[service_name] = {
                "type": spec_type,
                "type_name": spec_type_name,
                "param_name": spec_param_name,
            }

            init_annotations[spec_param_name] = Optional[spec_type]

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
            Initialize the App instance with optional service specifications.
            """
            # Initialize the specs dictionary
            self._specs: Dict[str, object] = {}  # type: ignore

            # Process spec parameters
            for service_name in self.__class__._service_descriptors:
                spec_param_name = f"{service_name}_spec"
                if spec_param_name in kwargs:
                    self._specs[service_name] = kwargs.pop(spec_param_name)

            # Call original __init__ if it exists
            if original_init:
                original_init(self, *args, **kwargs)
            else:
                # Find and call the appropriate parent __init__
                _call_parent_init(self, args, kwargs)

        # Add the generated methods to the namespace
        namespace["__init__"] = __init__

        # Store service descriptors on the class as a class variable with proper typing
        namespace["_service_descriptors"] = services
        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}
        namespace["__annotations__"]["_service_descriptors"] = ClassVar[
            Dict[str, ServiceDescriptor]
        ]

        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)

        # Generate parameter documentation
        param_docs: List[str] = []
        for service_name, info in spec_info.items():
            # Add parameter documentation with type information
            param_docs.append(
                f"\t{info['param_name']} (Optional[{info['type_name']}]): "
                f"Specification for the {service_name} service. "
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

        # Add parameters for each service spec
        for service_name, info in spec_info.items():
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
