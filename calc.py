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
    type: str
    special_mutations: tuple[str] | None = None


class Mutation(BaseModel):
    name: str
    color: Literal["灰色", "绿色", "蓝色", "金色", "彩色", "紫色"]
    multiplier: float


def main():
    with open("plants.json", "rb") as f:
        data = f.read()
        raw_list: list = orjson.loads(data)
        plants = list(map(Plant.model_validate, raw_list))

    with open("mutations.json", "rb") as f:
        data = f.read()
        raw_list: list = orjson.loads(data)
        mutations = list(map(Mutation.model_validate, raw_list))

    print(plants)
    print(mutations)


main()
