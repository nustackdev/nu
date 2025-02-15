from loomi.app.base import App
from loomi.service import Service, Spec

__all__ = ["AppCommonServices"]

class AppCommonServices(App):
    def add_service_dependency(self, name: str, spec: Spec) -> Service: ...
    def get_service_dependency(self, name: str) -> Service: ...
