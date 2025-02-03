# class AppMeta(type):
#     def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
#         # Create the model class
#         cls = super().__new__(mcs, name, bases, namespace)

#         # Create a transaction class dynamically with the same type hints
#         tx_namespace = {
#             "__annotations__": namespace.get("__annotations__", {}),
#             # Copy all Item descriptors
#             **{k: v for k, v in namespace.items() if isinstance(v, Item)},
#         }

#         # Create transaction class with proper type hints
#         tx_cls = type(f"{name}Transaction", (BaseTransaction,), tx_namespace)

#         # Store the transaction class on the model class
#         setattr(cls, "_transaction_class", tx_cls)

#         return cls
