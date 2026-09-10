from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticCase:
    """One generated MediLacra patient reality used by Disco Inferno.

    The child objects retain their normal MediLacra identifiers, so
    encounter_id remains the relationship that preserves grain.
    """

    patient: object
    encounters: tuple[object, ...]
    transactions: tuple[object, ...]
    observations: tuple[object, ...]
