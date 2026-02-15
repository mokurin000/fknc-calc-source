from typing import Literal

import orjson
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

BASE_MUTATIONS = ["星空", "流光", "水晶", "金", "银"]


class Plant(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    price_coefficient: float
    max_weight: float
    growth_speed: float
    type: Literal["普通", "月球"]
    special_mutations: tuple[str] | None = None


class Mutation(BaseModel):
    name: str
    color: Literal["灰色", "绿色", "蓝色", "金色", "彩色", "紫色"]
    multiplier: float


class PriceResult(BaseModel):
    base_factor: float
    special_factor: float
    mutate_factor: float
    weight_factor: float
    total_price: float


def calc_price(plant: Plant, weight: float, mutations: list[Mutation]) -> PriceResult:
    """
    根据给定的植物底价、重量、携带突变，

    计算其总价值与各项因数。
    """
    if not isinstance(plant, Plant):
        raise TypeError("无效输入类型")
    if weight > plant.max_weight or weight < 0.03 * plant.max_weight:
        raise Exception("无效的作物重量！")

    base_factor = 1
    special_factor = 1
    mutate_factor = 1

    for mutation in mutations:
        if not isinstance(mutation, Mutation):
            raise TypeError("无效输入类型")

        if mutation.name in BASE_MUTATIONS:
            base_factor = max(base_factor, mutation.multiplier)
            continue
        if mutation.name in plant.special_mutations:
            special_factor = max(special_factor, mutation.multiplier)
            continue
        mutate_factor += mutation.multiplier

    weight_factor = weight**1.5

    total_price = (
        round(plant.price_coefficient, 4)
        * weight_factor
        * base_factor
        * special_factor
        * mutate_factor
    )

    return PriceResult(
        base_factor=base_factor,
        weight_factor=weight_factor,
        special_factor=special_factor,
        mutate_factor=mutate_factor,
        total_price=total_price,
    )


def load_data() -> tuple[list[Plant], list[Mutation]]:
    with open("plants.json", "rb") as f:
        data = f.read()
        raw_list: list = orjson.loads(data)
        plants = list(map(Plant.model_validate, raw_list))

    with open("mutations.json", "rb") as f:
        data = f.read()
        raw_list: list = orjson.loads(data)
        mutations = list(map(Mutation.model_validate, raw_list))

    return plants, mutations
