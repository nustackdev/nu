"""Shim — use nu.ops, nu.interfaces, nu.context, etc. instead."""

from nu.interfaces.capabilities import *  # noqa: F403
from nu.interfaces.collections_abc import *  # noqa: F403
from nu.interfaces.types import *  # noqa: F403
from nu.interfaces.values import *  # noqa: F403
from nu.method import AutoInterface, method, prop
from nu.ops import *  # noqa: F403
from nu.ops.combiners import all_, and_, any_, none_, or_
from nu.ops.flows import (
    All,
    Any,
    Assert,
    AssertEmpty,
    AssertEquals,
    AssertExists,
    AssertGreaterOrEqual,
    AssertGreaterThan,
    AssertLessOrEqual,
    AssertLessThan,
    AssertMissing,
    AssertNotEmpty,
    AssertNotEquals,
    Debounce,
    Debug,
    Delay,
    DoWhile,
    Fold,
    ForEach,
    Forever,
    ForRange,
    If,
    Log,
    Parallel,
    Print,
    Race,
    Retry,
    Seq,
    SkipIfEmpty,
    SkipIfExists,
    SkipIfMissing,
    SkipIfNotEmpty,
    Switch,
    Throttle,
    Timeout,
    TryCatch,
    While,
)
from nu.ops import fn
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
from nu.transform.builtin import annotate_retries, annotate_steps, set_logger_name
from nu.utils import ensure_term, typed_value
