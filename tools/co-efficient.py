from pydantic import BaseModel


class PriceCo(BaseModel):
    price: int
    weight: float
    base: float = 1.0
    special: float = 1.0
    weather: float = 0.0
    """天气系数，不含加上的 1"""


def calculate_priceco(priceco: PriceCo) -> float:
    co_efficient = priceco.price / (
        priceco.special * priceco.base * priceco.weight**1.5 * (priceco.weather + 1.0)
    )
    return round(co_efficient, 4)


coefficient_map: dict[str, list[PriceCo]] = {
    "红包果": [
        PriceCo(
            price=79946,
            weight=0.21,
            weather=9.0,
        ),
        PriceCo(
            price=70223,
            weight=0.18,
            weather=10.0,
        ),
    ],
}

if __name__ == "__main__":
    for crop, data_list in coefficient_map.items():
        avg = sum(map(calculate_priceco, data_list)) / len(data_list)
        print(f"{crop}: {avg:.4f}")
