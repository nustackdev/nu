from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .bases import AppAsyncBase, AppBase, AppSyncBase

AppType: TypeAlias = "AppSyncBase | AppAsyncBase | AppBase"
