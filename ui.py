import streamlit as st
from fknc_calc import load_data, calc_price, BASE_MUTATIONS, Plant
from pydantic import ValidationError


def compute_all_special_mutations(plants: list[Plant]) -> set[str]:
    return {
        name
        for plant in plants
        if plant.special_mutations
        for name in plant.special_mutations
    }


def main():
    # 加载植物和突变数据
    plants, mutations = load_data()

    # 筛选特殊突变
    ALL_SPECIAL_MUTATIONS = compute_all_special_mutations(plants)

    # 提供作物选择
    plant_names = [plant.name for plant in plants]
    plant_name = st.selectbox("选择作物", plant_names)

    # 获取选择的植物对象
    selected_plant = next(plant for plant in plants if plant.name == plant_name)

    # 显示植物详细信息
    st.write(f"作物名称: {selected_plant.name}")
    st.write(f"作物类型: {selected_plant.type}")
    st.write(f"价格系数: {selected_plant.price_coefficient}")
    st.write(f"最大重量: {selected_plant.max_weight}")

    # 基础突变选择
    base_mutations = [
        mutation for mutation in mutations if mutation.name in BASE_MUTATIONS
    ]
    base_mutation_names = [mutation.name for mutation in base_mutations]
    selected_base_mutation_name = st.selectbox("选择基础突变", base_mutation_names)

    # 获取选中的基础突变
    selected_base_mutation = next(
        mutation
        for mutation in base_mutations
        if mutation.name == selected_base_mutation_name
    )

    st.write(
        f"选择的基础突变: {selected_base_mutation.name}, 颜色: {selected_base_mutation.color}, 乘数: {selected_base_mutation.multiplier}"
    )

    # 选择其他突变
    other_mutations = [
        mutation
        for mutation in mutations
        if mutation.name not in BASE_MUTATIONS
        and mutation.name not in ALL_SPECIAL_MUTATIONS
    ]
    other_mutation_names = [mutation.name for mutation in other_mutations]
    # 特殊突变选择
    special = (
        list(selected_plant.special_mutations)
        if selected_plant.special_mutations is not None
        else []
    )

    selectable_names = special + other_mutation_names

    selected_mutations = st.multiselect(
        "选择其他突变 (可多选)",
        selectable_names,
        default=[],
    )

    # 输入作物重量
    weight = st.number_input(
        f"输入作物重量 (最大: {selected_plant.max_weight}kg)",
        min_value=0.03 * selected_plant.max_weight,
        max_value=selected_plant.max_weight,
        value=0.03 * selected_plant.max_weight,
    )

    try:
        # 构建突变列表
        mutations_to_apply = [
            selected_base_mutation,
            *[
                mutation
                for mutation in mutations
                if mutation.name in selected_mutations
            ],
        ]

        # 计算价格
        price_result = calc_price(selected_plant, weight, mutations_to_apply)

        # 显示计算结果
        st.write(f"基础因子: {price_result.base_factor}")
        st.write(f"重量因子: {price_result.weight_factor:.4f}")
        st.write(f"特殊因子: {price_result.special_factor}")
        st.write(f"突变因子: {price_result.mutate_factor}")
        st.write(f"总价格: {price_result.total_price:.0f}")

    except ValidationError as e:
        st.error(f"输入数据无效: {e}")
    except Exception as e:
        st.error(f"发生错误: {e}")


if __name__ == "__main__":
    main()
