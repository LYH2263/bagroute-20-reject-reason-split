"""Route-order bag packing with weight + volume caps; reject when exceed."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RejectCategory(str, Enum):
    WEIGHT_ONLY = "weight_only"          # 仅超重
    VOLUME_ONLY = "volume_only"          # 仅超体积
    WEIGHT_AND_VOLUME = "weight_volume"  # 同时超重超体积


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""


@dataclass
class Bag:
    bag_index: int
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0


@dataclass(frozen=True)
class Reject:
    item: StopItem
    reason: str
    category: RejectCategory | None


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[Reject]


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
    )


def classify_reject(
    item: StopItem, max_weight: float, max_volume: float
) -> RejectCategory | None:
    """Return the reject category, or None when the item is within both caps."""
    over_weight = item.weight_kg > max_weight
    over_volume = item.volume_l > max_volume
    if over_weight and over_volume:
        return RejectCategory.WEIGHT_AND_VOLUME
    if over_weight:
        return RejectCategory.WEIGHT_ONLY
    if over_volume:
        return RejectCategory.VOLUME_ONLY
    return None


def reject_reason(
    item: StopItem, category: RejectCategory, max_weight: float, max_volume: float
) -> str:
    if category is RejectCategory.WEIGHT_ONLY:
        return f"仅超重：{item.weight_kg}kg > 限重 {max_weight}kg"
    if category is RejectCategory.VOLUME_ONLY:
        return f"仅超体积：{item.volume_l}L > 限体积 {max_volume}L"
    return (
        f"同时超重超体积：{item.weight_kg}kg > 限重 {max_weight}kg；"
        f"{item.volume_l}L > 限体积 {max_volume}L"
    )


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
) -> PackResult:
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[Reject] = []
    current: Bag | None = None

    for item in ordered:
        category = classify_reject(item, max_weight, max_volume)
        if category is not None:
            rejects.append(
                Reject(item, reject_reason(item, category, max_weight, max_volume), category)
            )
            continue

        if current is None or not can_fit(current, item, max_weight, max_volume):
            current = Bag(bag_index=len(bags) + 1)
            bags.append(current)

        if not can_fit(current, item, max_weight, max_volume):
            # defensive: unreachable for an item within single-item caps
            rejects.append(Reject(item, "无法装入新袋", None))
            continue

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l

    return PackResult(bags=bags, rejects=rejects)
