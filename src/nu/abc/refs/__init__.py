"""Shim — use nu.context instead."""

from nu.context.attr_refs import PrimRef
from nu.context.attr_refs import PrimRef as IntRef
from nu.context.attr_refs import PrimRef as FloatRef
from nu.context.attr_refs import PrimRef as StrRef
from nu.context.attr_refs import PrimRef as BoolRef
from nu.context.attr_refs import PrimRef as BytesRef
from nu.context.attr_refs import PrimRef as AnyRef
from nu.context.attr_ops import PrimExistsOp, PrimGetOp
from nu.context.service_refs import ServiceRef
from nu.context.service_ops import ServiceExistsOp, ServiceGetOp
