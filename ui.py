from functools import partial, reduce


import streamlit as st
from pypinyin import lazy_pinyin
from fknc_calc import Mutation, load_data, calc_price, BASE_MUTATIONS, Plant
from fknc_calc.rules import is_mutation_allowed
from pydantic import ValidationError


def compute_all_special_mutations(plants: list[Plant]) -> set[str]:
    return {
        name
        for plant in plants
        if plant.special_mutations
        for name in plant.special_mutations
    }


def display_name_of_mutation(
    specials: set[str],
    mutations: list[Mutation],
    name: str,
):
    try:
        mutation = next(mutation for mutation in mutations if mutation.name == name)
    except StopIteration:
        if name == "无":
            return "x1 无"
        return name

    factor = mutation.multiplier
    if factor == int(factor):
        num_fmt = f"{factor:.0f}"
    else:
        num_fmt = f"{factor:.1f}"
    if name in specials or name in BASE_MUTATIONS:
        return f"x{num_fmt} {name}"
    else:
        return f"+{num_fmt} {name}"


def main():
    # 加载植物和突变数据
    if "loaded-data" in st.session_state:
        plants, mutations = st.session_state["loaded-data"]
    else:
        plants, mutations = load_data()
        st.session_state["loaded-data"] = (plants, mutations)

    # 筛选特殊突变
    ALL_SPECIAL_MUTATIONS = compute_all_special_mutations(plants)

    display_name = partial(
        display_name_of_mutation,
        ALL_SPECIAL_MUTATIONS,
        mutations,
    )

    # 基础突变选择
    base_mutations = [
        mutation for mutation in mutations if mutation.name in BASE_MUTATIONS
    ]
    base_mutation_names = BASE_MUTATIONS[:]

    # 显示植物详细信息
    st.markdown("#### 作物信息")
    with st.container(horizontal=True):
        # 提供作物选择
        plant_names = [
            p.name
            for p in sorted(
                (plant for plant in plants),
                key=lambda p: lazy_pinyin(p.name),
            )
        ]
        plant_name = st.selectbox("选择作物", plant_names, label_visibility="collapsed")

        # 获取选择的植物对象
        selected_plant = next(plant for plant in plants if plant.name == plant_name)
        if selected_plant.type != "月球":
            base_mutation_names.remove("星空")

        selected_base_mutation_name = st.selectbox(
            "",
            ["无"] + base_mutation_names,
            format_func=display_name,
            label_visibility="collapsed",
        )

        st.write(f"作物类型: {selected_plant.type}")
        st.write(
            "生长速度: " + (f"{selected_plant.growth_speed}".rstrip(".0") or "未知")
        )

    # 输入作物重量
    weight = st.number_input(
        f"作物重量 (最大: {selected_plant.max_weight}kg)",
        min_value=0.03 * selected_plant.max_weight,
        max_value=selected_plant.max_weight,
        value=0.03 * selected_plant.max_weight,
    )

    # 获取选中的基础突变
    if selected_base_mutation_name != "无":
        selected_base_mutation = next(
            mutation
            for mutation in base_mutations
            if mutation.name == selected_base_mutation_name
        )
    else:
        selected_base_mutation = None

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

    previously_selected: list = st.session_state.get("selected-mutations", [])

    st.markdown("#### 突变词条")
    selected_mutations = st.multiselect(
        "其他突变",
        list(
            filter(
                partial(
                    is_mutation_allowed,
                    previously_selected,
                    selected_plant,
                ),
                selectable_names,
            )
        ),
        default=[],
        key="selected-mutations",
        format_func=display_name,
    )

    try:
        # 构建突变列表
        mutations_to_apply = [
            mutation for mutation in mutations if mutation.name in selected_mutations
        ]

        if selected_base_mutation is not None:
            mutations_to_apply.append(selected_base_mutation)

        # 计算价格
        price_result = calc_price(selected_plant, weight, mutations_to_apply)
        price = price_result.total_price
        if price < 1e4:
            price_pretty = None
        elif price < 1e8:
            price_pretty = f"{price / 1e4:.2f}".rstrip("0") + " 万"
        else:
            price_pretty = f"{price / 1e8:.2f}".rstrip("0") + "亿"

        st.markdown(
            """<style>
span.katex {
    text-align: left !important;
}
</style>""",
            unsafe_allow_html=True,
        )

        latex_expression = r"""
        \text{总价格} \\

        = \text{作物基价} \times \text{重量因数} \times
        \text{基础突变} \times \text{专属突变} \times \left(1 + \text{常规突变}\right) \\

        = \left( \text{%.4f} \times \text{%.2f}^{1.5} \right) \times \left(
        \text{%.1f} \times \text{%.1f} \times \text{%.1f} \right) \\

        = \text{%.4f} \times \text{%.1f} \\

        = \text{%.0f}
        """ % (
            selected_plant.price_coefficient,
            weight,
            price_result.base_factor,
            price_result.special_factor,
            price_result.mutate_factor + 1,
            selected_plant.price_coefficient * price_result.weight_factor,
            reduce(
                lambda a, b: a * b,
                [
                    price_result.base_factor,
                    price_result.special_factor,
                    price_result.mutate_factor + 1,
                ],
            ),
            price,
        )
        if price_pretty is not None:
            latex_expression += r""" \\
        \approx %s""" % (price_pretty,)

        st.latex(latex_expression)

    except ValidationError as e:
        st.error(f"输入数据无效: {e}")
    except Exception as e:
        st.error(f"发生错误: {e}")


if __name__ == "__main__":
    main()
