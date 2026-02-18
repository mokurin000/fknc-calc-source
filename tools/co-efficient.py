import math
from typing import List, Dict
from pydantic import BaseModel


class PriceCo(BaseModel):
    price: int
    weight: float
    base: float = 1.0
    special: float = 1.0
    weather: float = 0.0
    """
    weather 不含 +1
    实际计算时使用 (weather + 1)
    """


# =========================
# 基础公式
# =========================


def compute_x(p: PriceCo) -> float:
    return p.special * p.base * p.weight**1.5 * (p.weather + 1.0)


def predict_price(p: PriceCo, k: float) -> float:
    return compute_x(p) * k


# =========================
# 简单平均值
# =========================


def coefficient_mean(data_list: List[PriceCo]) -> float:
    nums = [p.price / compute_x(p) for p in data_list]
    return sum(sorted(nums)) / len(nums)


# =========================
# 最小化 Σ(kX - price)^2
# =========================


def coefficient_least_squares(data_list: List[PriceCo]) -> float:
    xs = [compute_x(p) for p in data_list]
    numerator = sum(x * p.price for x, p in zip(xs, data_list))
    denominator = sum(x * x for x in xs)

    if denominator == 0:
        raise ValueError("Denominator is zero")

    return numerator / denominator


# =========================
# log(price) = log(k) + log(X)
# =========================


def coefficient_log_regression(data_list: List[PriceCo]) -> float:
    logs = []

    for p in data_list:
        x = compute_x(p)

        if p.price <= 0 or x <= 0:
            raise ValueError("Log regression requires positive values")

        logs.append(math.log(p.price) - math.log(x))

    log_k = sum(logs) / len(logs)
    return math.exp(log_k)


# =========================
# 误差评估
# =========================


def evaluate(data_list: List[PriceCo], k: float) -> Dict[str, float]:
    rel_sq_error = 0.0

    for p in data_list:
        predicted = predict_price(p, k)

        rel_sq_error += ((predicted - p.price) / p.price) ** 2

    return {
        "相对平方误差": rel_sq_error,
    }


# =========================
# 数据
# =========================

coefficient_map: Dict[str, List[PriceCo]] = {
    "月莓": [
        PriceCo(
            price=13937700,
            weight=3.20,
            weather=30.0,
        )
    ],
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
        PriceCo(
            price=45341,
            weight=0.17,
            weather=7.0,
        ),
        PriceCo(
            price=191410,
            weight=0.17,
            weather=10.0,
            base=3.0,
        ),
    ],
    "星叶菜": [
        PriceCo(
            price=20815600,  # ..
            base=10.0,
            weight=6.31,
            weather=32.0,
        ),
        PriceCo(
            price=4169000,  # ..
            base=30.0,
            weight=1.04,
            weather=32.0,
        ),
        PriceCo(
            price=1413400,  # ..
            base=20.0,
            weight=0.82,
            weather=23.0,
        ),
        PriceCo(
            price=2459232,
            base=20.0,
            weather=13.0,
            weight=1.70,
        ),
        PriceCo(
            price=6615,
            weight=0.48,
            weather=4.0,
        ),
        PriceCo(
            price=5816,
            weight=0.44,
            weather=4.0,
        ),
    ],
    "幻月花": [
        PriceCo(
            price=18835500,  # ..
            base=20.0,
            weight=2.03,
            weather=38.0,
        ),
        PriceCo(
            price=17663800,  # ..
            base=20.0,
            weight=2.37,
            weather=28.0,
        ),
    ],
    "月兔": [
        PriceCo(
            price=66564,
            weight=0.90,
            weather=6.0,
        ),
        PriceCo(
            price=96906,
            weight=1.15,
            weather=6.0,
        ),
    ],
    "大王菊": [
        PriceCo(
            price=1394100,  # ..
            weight=0.68,
            base=20,
            weather=4,
        ),
        PriceCo(
            price=1951700,  # ..
            weight=0.68,
            base=20,
            weather=6,
        ),
    ],
}


# =========================
# 主程序
# =========================


def run_analysis(name: str, data_list: List[PriceCo]) -> None:
    print(f"\n===== {name} =====")

    k_mean = coefficient_mean(data_list)
    k_ls = coefficient_least_squares(data_list)
    k_log = coefficient_log_regression(data_list)

    print(f"最小二乘 k: \t{k_ls:.6f}")
    print(f"log 回归 k: \t{k_log:.6f}")
    print(f"平均取值 k: \t{k_mean:.6f}")

    print("\n--- 误差分析 ---")

    for method_name, k in [
        ("最小二乘", k_ls),
        ("log 回归", k_log),
        ("平均取值", k_mean),
    ]:
        err = evaluate(data_list, k)
        print(f"\n[{method_name}]")
        print(f"相对平方误差和(%): {err['相对平方误差'] * 10000:.6f}")

        print("各样本差额:")
        for p in data_list:
            predicted = predict_price(p, k)
            diff = (predicted - p.price) / p.price
            print(
                f"  weight={p.weight:.2f}, expected {p.price}, got {predicted:.0f} ({diff * 100:+.2f}%)"
            )


if __name__ == "__main__":
    for crop, data_list in coefficient_map.items():
        run_analysis(crop, data_list)
