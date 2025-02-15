from loomi.service.base import Service, ServiceState

__all__ = ["ServiceCommonInitializer"]

class ServiceCommonInitializer(Service):
    @property
    def service_state(self) -> ServiceState: ...
    @property
    def is_initialized(self) -> bool: ...
