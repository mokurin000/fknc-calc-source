from importlib.resources import files, as_file
from typing import Literal

import orjson
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

BASE_MUTATIONS = [
    "银",
    "金",
    "水晶",
    "流光",
    "星空",  # 月球作物专属基础突变
]


class Plant(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    price_coefficient: float
    max_weight: float
    growth_speed: float
    """每秒增长的百分比/kg * 100"""
    type: Literal["普通", "月球"]
    special_mutations: tuple[str] | None = None


class Mutation(BaseModel):
    name: str
    color: Literal["灰色", "绿色", "蓝色", "金色", "彩色", "紫色"]
    multiplier: float


class PriceResult(BaseModel):
    base_factor: float
    """基础突变因数"""
    special_factor: float
    """独占突变因数"""
    weight_factor: float
    """重量因数"""
    mutate_factor: float
    """常规突变因数之和，不带额外的 1"""
    total_price: float


def calc_price(plant: Plant, weight: float, mutations: list[Mutation]) -> PriceResult:
    """
    根据给定的植物底价、重量、携带突变，

    计算其总价值与各项因数。
    """
    if not isinstance(plant, Plant):
        raise TypeError("无效输入类型")
    if weight > plant.max_weight:
        raise Exception("无效的作物重量！")

    base_factor = 1
    special_factor = 1
    mutate_factor = 0

    for mutation in mutations:
        if not isinstance(mutation, Mutation):
            raise TypeError("无效输入类型")

        if mutation.name in BASE_MUTATIONS:
            base_factor = max(base_factor, mutation.multiplier)
            continue
        if (
            plant.special_mutations is not None
            and mutation.name in plant.special_mutations
        ):
            special_factor = max(special_factor, mutation.multiplier)
            continue
        mutate_factor += mutation.multiplier

    weight_factor = weight**1.5

    total_price = (
        round(plant.price_coefficient, 4)
        * weight_factor
        * base_factor
        * special_factor
        * (1 + mutate_factor)
    )

    return PriceResult(
        base_factor=base_factor,
        weight_factor=weight_factor,
        special_factor=special_factor,
        mutate_factor=mutate_factor,
        total_price=total_price,
    )


def load_data() -> tuple[list[Plant], list[Mutation]]:
    base_dir = files("fknc_calc")
    with (
        as_file(base_dir / "plants.json") as plants_file,
        as_file(base_dir / "mutations.json") as mutations_file,
    ):
        with open(plants_file, "rb") as f:
            data = f.read()
            raw_list: list = orjson.loads(data)
            plants = list(map(Plant.model_validate, raw_list))

        with open(mutations_file, "rb") as f:
            data = f.read()
            raw_list: list = orjson.loads(data)
            mutations = list(map(Mutation.model_validate, raw_list))

    return plants, mutations


def mutation_name_map(mutations: list[Mutation]) -> dict[str, Mutation]:
    return {mutation.name: mutation for mutation in mutations}
