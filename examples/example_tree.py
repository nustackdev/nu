from pathlib import Path

from everyshape.adapters import BinaryCodec, RocksDBStorage
from everyshape.container import Container, ContainerProtocol, ContainerStructure


def main() -> None:
    """Demo."""
    with RocksDBStorage(path=Path(".db_tree"), codec=BinaryCodec()) as storage:
        with storage.transaction() as tx:
            alice = Container.create(
                ("/", "alice"),
                tx,
                ContainerStructure(1),
                ContainerProtocol.MUTABLE,
            )
            alice.set_child_primitive("name", "Alice")
            parents = alice.create_child_container(
                "parents", ContainerStructure(1), ContainerProtocol.MUTABLE
            )
            parents.set_child_primitive(0, "Donald")
            parents.set_child_primitive(1, "Mary")

        with storage.snapshot() as snap:
            alice = Container.get(
                ("/", "alice"),
                snap,
            )
            for key, value in alice.list_children():
                print(f"{key}: {value}")

        with storage.transaction() as tx:
            tmp = Container.create(
                ("/", "tmp"),
                tx,
                ContainerStructure(1),
                ContainerProtocol.MUTABLE,
            )
            print(tmp.info())
            print(list(tmp.list_child_keys()))


if __name__ == "__main__":
    main()
