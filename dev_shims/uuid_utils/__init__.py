"""Pure-Python uuid_utils shim when native wheel fails on this host."""
from __future__ import annotations

from uuid import (
    NAMESPACE_DNS,
    NAMESPACE_OID,
    NAMESPACE_URL,
    NAMESPACE_X500,
    RESERVED_FUTURE,
    RESERVED_MICROSOFT,
    RESERVED_NCS,
    RFC_4122,
    UUID,
    SafeUUID,
    getnode,
    uuid1,
    uuid3,
    uuid4,
    uuid5,
    uuid7 as _stdlib_uuid7,
)

__version__ = "0.17.0+stdlib-shim"

NIL = UUID("00000000-0000-0000-0000-000000000000")
MAX = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")


def uuid6(node=None, timestamp=None):
    raise NotImplementedError("uuid6 is not available in the stdlib shim")


def uuid7(timestamp=None, nanos=None):
    return _stdlib_uuid7()


def uuid8(bytes):
    raise NotImplementedError("uuid8 is not available in the stdlib shim")


def _uuid4_int():
    return uuid4().int


def _uuid7_int(timestamp=None, nanos=None):
    return uuid7(timestamp, nanos).int


__all__ = [
    "MAX",
    "NAMESPACE_DNS",
    "NAMESPACE_OID",
    "NAMESPACE_URL",
    "NAMESPACE_X500",
    "NIL",
    "RESERVED_FUTURE",
    "RESERVED_MICROSOFT",
    "RESERVED_NCS",
    "RFC_4122",
    "UUID",
    "SafeUUID",
    "__version__",
    "getnode",
    "uuid1",
    "uuid3",
    "uuid4",
    "uuid5",
    "uuid6",
    "uuid7",
    "uuid8",
    "_uuid4_int",
    "_uuid7_int",
]
