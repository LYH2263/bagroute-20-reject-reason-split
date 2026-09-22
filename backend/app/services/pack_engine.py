"""Route-order bag packing with weight + volume caps; reject when exceed."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RejectCategory(str, Enum):
    """拒收分档：仅超重 / 仅超体积 / 同时超重超体积。"""

    WEIGHT_ONLY = "weight_only"
    VOLUME_ONLY = "volume_only"
    WEIGHT_AND_VOLUME = "weight_and_volume"


# 分档的中文展示文案（原因列与前端标签共用）
CATEGORY_LABELS: dict[RejectCategory, str] = {
    RejectCategory.WEIGHT_ONLY: "仅超重",
    RejectCategory.VOLUME_ONLY: "仅超体积",
    RejectCategory.WEIGHT_AND_VOLUME: "超重且超体积",
}


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
    category: RejectCategory
    reason: str


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[Reject]


def classify_reject(
    item: StopItem, max_weight: float, max_volume: float
) -> RejectCategory:
    over_weight = item.weight_kg > max_weight
    over_volume = item.volume_l > max_volume
    if over_weight and over_volume:
        return RejectCategory.WEIGHT_AND_VOLUME
    if over_weight:
        return RejectCategory.WEIGHT_ONLY
    return RejectCategory.VOLUME_ONLY


def reject_reason(
    item: StopItem, category: RejectCategory, max_weight: float, max_volume: float
) -> str:
    if category is RejectCategory.WEIGHT_ONLY:
        return f"仅超重：{item.weight_kg}kg > 上限 {max_weight}kg"
    if category is RejectCategory.VOLUME_ONLY:
        return f"仅超体积：{item.volume_l}L > 上限 {max_volume}L"
    return (
        f"超重且超体积：{item.weight_kg}kg > {max_weight}kg，"
        f"{item.volume_l}L > {max_volume}L"
    )


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
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
        if item.weight_kg > max_weight or item.volume_l > max_volume:
            category = classify_reject(item, max_weight, max_volume)
            rejects.append(
                Reject(item, category, reject_reason(item, category, max_weight, max_volume))
            )
            continue

        if current is None or not can_fit(current, item, max_weight, max_volume):
            current = Bag(bag_index=len(bags) + 1)
            bags.append(current)

        # 单件不超限时空袋必能容纳，直接装入
        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l

    return PackResult(bags=bags, rejects=rejects)
