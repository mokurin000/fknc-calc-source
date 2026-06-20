from fknc_calc import load_data

crops, _ = load_data()
print("作物 | 价格系数 | 最大重量 | 种子价值")
print("---: | :---: | :--- | :--:")
for crop in crops:
    print(
        f"{crop.name} | {crop.price_coefficient:.4f} | {crop.max_weight} | {crop.seed_price}"
    )
