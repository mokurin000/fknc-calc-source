from functools import partial
from collections import defaultdict

import streamlit as st
from pypinyin import lazy_pinyin
from fknc_calc import (
    Mutation,
    load_data,
    calc_price,
    BASE_MUTATIONS,
    Plant,
    mutation_name_map,
)
from fknc_calc.rules import RECIPES, is_mutation_disabled, MOON_ONLY
from pydantic import ValidationError


def show_calculation(
    base_mutation: Mutation | None,
    mutations: list[str],
    mutations_map: dict[str, Mutation],
    crop: Plant,
    weight: float,
):
    # 构建突变列表
    mutations_to_apply = [mutations_map[name] for name in mutations]

    if base_mutation is not None:
        mutations_to_apply.append(base_mutation)

    # 计算价格
    price_result = calc_price(crop, weight, mutations_to_apply)
    price = price_result.total_price
    if price < 1e4:
        price_pretty = None
    elif price < 1e8:
        price_pretty = f"{price / 1e4:.2f}".rstrip(".0") + " 万"
    else:
        price_pretty = f"{price / 1e8:.2f}".rstrip(".0") + "亿"

    st.markdown(
        """<style>
span.katex {
text-align: left !important;
}
</style>""",
        unsafe_allow_html=True,
    )

    # 除天气突变以外的因数之积
    mid_factor = (
        price_result.weight_factor
        * price_result.base_factor
        * price_result.special_factor
    )
    latex_expression = rf"""
    \text{{总价格}} \\

    = \text{{作物基价}} \times \text{{重量因数}} \times
    \text{{基础突变}} \times \text{{专属突变}} \times \left(1 + \text{{常规突变}}\right) \\

    = \left( \text{crop.price_coefficient:.4f} \times
    \left( \text{weight:.2f}^{{1.5}} \times \text{price_result.base_factor:.1f} \times
    \text{price_result.special_factor:.1f} \right) \right) \times
    \text{price_result.mutate_factor + 1:.1f} \\

    = \left( \text{crop.price_coefficient:.4f} \times
    \text{mid_factor:.4f} \right) \times
    \text{(price_result.mutate_factor + 1):.1f} \\

    = \text{crop.price_coefficient * mid_factor:.4f} \times
    \text{(price_result.mutate_factor + 1):.1f} \\

    = \text{price:.0f}
    """
    if price_pretty is not None:
        latex_expression += r""" \\
    \approx %s""" % (price_pretty,)

    st.latex(latex_expression)


def time_format(secs_per_percent: float) -> str:
    total_time = int(round(secs_per_percent * 100, 0))

    if total_time >= 3600:
        total_hours = total_time // 3600
        total_mins = (total_time % 3600) // 60
    elif total_time >= 60:
        total_hours = None
        total_mins = total_time // 60
    else:
        total_hours = None
        total_mins = None
    total_secs = total_time % 60

    return (
        (f"{total_hours:02}时" if total_hours else "")
        + (f"{total_mins:02}分" if total_mins else "")
        + (f"{total_secs:02}秒" if total_secs else "")
    ).lstrip("0")


def compute_all_special_mutations(plants: list[Plant]) -> set[str]:
    return {
        name
        for plant in plants
        if plant.special_mutations
        for name in plant.special_mutations
    }


def display_name_of_mutation(
    specials: set[str],
    mutations_map: dict[str, Mutation],
    name: str,
):
    if name == "无":
        return "x1 无"

    factor = mutations_map[name].multiplier
    if factor == int(factor):
        num_fmt = f"{factor:.0f}"
    else:
        num_fmt = f"{factor:.1f}"
    if name in specials or name in BASE_MUTATIONS:
        return f"x{num_fmt} {name}"
    else:
        return f"+{num_fmt} {name}"


def input_weight_slider_input(
    min_weight: float,
    max_weight: float,
    plant_name: str,
) -> float:
    default_value = max_weight * 0.05

    slider_key = f"weight-{plant_name}-slider"
    number_key = f"weight-{plant_name}-number-input"
    st.session_state[slider_key] = st.session_state.get(slider_key, default_value)
    st.session_state[number_key] = st.session_state.get(number_key, default_value)

    st.markdown(
        f"<span style='display: flex; justify-content: center;'>作物重量 ({min_weight:.2f}~{max_weight} kg)</span>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns([7, 2])
    with col1:
        st.slider(
            "作物重量",
            min_value=min_weight,
            max_value=max_weight,
            step=0.01,
            key=slider_key,
            on_change=lambda: st.session_state.update(
                {number_key: st.session_state[slider_key]}
            ),
            label_visibility="collapsed",
        )
    with col2:
        weight = st.number_input(
            "作物重量",
            min_value=min_weight,
            max_value=max_weight,
            step=0.01,
            key=number_key,
            on_change=lambda: st.session_state.update(
                {slider_key: st.session_state[number_key]}
            ),
            label_visibility="collapsed",
            width="stretch",
        )
        return weight


def main():
    # 加载植物和突变数据
    if "loaded-data" in st.session_state:
        plants, mutations, mutations_map = st.session_state["loaded-data"]
    else:
        plants, mutations = load_data()
        mutations_map: dict[str, Mutation] = mutation_name_map(mutations)
        st.session_state["loaded-data"] = (plants, mutations, mutations_map)

    # 筛选特殊突变
    ALL_SPECIAL_MUTATIONS = compute_all_special_mutations(plants)

    display_name = partial(
        display_name_of_mutation,
        ALL_SPECIAL_MUTATIONS,
        mutations_map,
    )

    base_mutation_names = BASE_MUTATIONS[:]

    # 显示植物详细信息

    st.markdown(
        """
    <span style='display: flex; justify-content: center;'>
       <h4>作物信息</h4>
    </span>
""",
        unsafe_allow_html=True,
    )
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
            "基础突变",
            ["无"] + base_mutation_names,
            format_func=display_name,
            label_visibility="collapsed",
        )

        st.write(f"作物类型: {selected_plant.type}")

    speed_text = "按速度"
    weight_text = "按重量"
    disable_speed = selected_plant.growth_speed == 0
    if (
        st.selectbox(
            "生长速度",
            [weight_text, speed_text],
            label_visibility="collapsed",
            help="速度为每多少秒长一百分比",
            disabled=disable_speed,
        )
        == weight_text
    ):
        # 输入作物重量
        min_weight = round(selected_plant.max_weight / 34, 2)
        weight = input_weight_slider_input(
            min_weight,
            max_weight=selected_plant.max_weight,
            plant_name=selected_plant.name,
        )

        if not disable_speed:
            secs_per_percent = weight * selected_plant.growth_speed / 100

            st.write(
                f"速度：{secs_per_percent:.1f} 秒/%，生长时间：{time_format(secs_per_percent)}",
            )
    else:
        # 输入生长速度
        min_speed = round(
            selected_plant.growth_speed * selected_plant.max_weight * 0.03 / 100, 1
        )
        max_speed = round(
            selected_plant.growth_speed * selected_plant.max_weight / 100, 2
        )

        label = f"生长速度 ({min_speed:.1f}~{max_speed:.2f}s/%)"
        st.markdown(
            f"""
    <span style='display: flex; justify-content: center;'>
       {label}
    </span>
""",
            unsafe_allow_html=True,
        )
        secs_per_percent = st.number_input(
            "生长速度",
            min_value=min_speed,
            max_value=max_speed,
            value=min_speed,
            step=0.01,
            format="%.2f",
            help="每百分比生长进度需要的秒数",
            label_visibility="collapsed",
        )
        percent = secs_per_percent / max_speed
        weight = selected_plant.max_weight * percent
        st.write(f"重量：{weight:.2f} kg，生长时间：{time_format(secs_per_percent)}")

    # 获取选中的基础突变
    if selected_base_mutation_name != "无":
        selected_base_mutation = mutations_map[selected_base_mutation_name]
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

    selectable_names = other_mutation_names
    if selected_plant.type != "月球":
        for name in MOON_ONLY:
            if name in selectable_names:
                selectable_names.remove(name)

    st.markdown(
        """
    <span style='display: flex; justify-content: center;'>
       <h4>突变词条</h4>
    </span>
""",
        unsafe_allow_html=True,
    )

    selected_mutations: set[str] = st.session_state.get("selected-mutations", set())

    # workaround for recipes condition
    # note: RECIPES must stay the dependency order.
    count = 0
    for recipe in RECIPES:
        mutation = recipe["result"]
        if mutation in selectable_names:
            count += 1

            selectable_names.remove(mutation)
            selectable_names.insert(0, mutation)

    selectable_names = selectable_names[:count] + selectable_names[: count - 1 : -1]

    # 处理剩下的顺序
    selectables = special + selectable_names

    cols_len = 5
    cols = st.columns([1] * cols_len)
    col_items: dict[int, list[str]] = defaultdict(list)

    for i, mutation_name in enumerate(selectables):
        col_items[i % cols_len].append(mutation_name)

    for i, items in col_items.items():
        with cols[i]:
            for mutation_name in items:
                disabled = is_mutation_disabled(
                    selected_mutations,
                    plant=selected_plant,
                    new_mutation=mutation_name,
                )

                fmt_name = display_name(mutation_name)
                new_state = st.checkbox(
                    fmt_name,
                    disabled=disabled,
                )

                if new_state and not disabled:
                    selected_mutations.add(mutation_name)
                else:
                    if mutation_name in selected_mutations:
                        selected_mutations.remove(mutation_name)

    st.session_state["selected-mutations"] = selected_mutations

    try:
        show_calculation(
            base_mutation=selected_base_mutation,
            mutations=selected_mutations,
            mutations_map=mutations_map,
            crop=selected_plant,
            weight=weight,
        )

    except ValidationError as e:
        st.error(f"输入数据无效: {e}")
    except Exception as e:
        st.error(f"发生错误: {e}")


if __name__ == "__main__":
    main()
