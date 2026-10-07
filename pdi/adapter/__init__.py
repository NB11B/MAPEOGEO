"""PDI-135M Software Reference Adapter Package.

Provides deterministic validation, canonical binary encoding/decoding,
and host transport protocol management for the MAPEOGEO FPGA fabric.
"""

from pdi.adapter.schema_validator import PDISchemaValidator, ValidationResult
from pdi.adapter.packet_codec import (
    PDIPacketCodec,
    ProposalPacket,
    DispositionPacket,
    PacketType,
    CommitOutcome,
    ReasonCode,
)
from pdi.adapter.host_transport import PDIHostSession

__all__ = [
    "PDISchemaValidator",
    "ValidationResult",
    "PDIPacketCodec",
    "ProposalPacket",
    "DispositionPacket",
    "PacketType",
    "CommitOutcome",
    "ReasonCode",
    "PDIHostSession",
]
