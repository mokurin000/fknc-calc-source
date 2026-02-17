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


def input_by_weight(selected_plant: Plant) -> float:
    # 输入作物重量
    min_weight = round(selected_plant.max_weight / 34, 2)
    weight = num_slider_input(
        min_value=min_weight,
        max_value=selected_plant.max_weight,
        plant_name=selected_plant.name,
    )

    return weight


def input_by_percent(selected_plant: Plant) -> float:
    percent = num_slider_input(
        min_value=3.0,
        max_value=100.0,
        plant_name=selected_plant.name,
        step=0.1,
        key_type="percent",
        a11y_label="重量百分比",
        unit="%",
        format="%.1f",
    )
    weight = round(percent * selected_plant.max_weight / 100, 2)
    return weight


def input_by_speed(selected_plant: Plant) -> float:
    # 输入生长速度
    min_speed = round(
        selected_plant.growth_speed * selected_plant.max_weight * 0.03 / 100, 1
    )
    max_speed = round(selected_plant.growth_speed * selected_plant.max_weight / 100, 2)

    secs_per_percent = num_slider_input(
        min_value=min_speed,
        max_value=max_speed,
        plant_name=selected_plant.name,
        key_type="speed",
        a11y_label="生长速度",
        unit="s/%",
    )
    percent = secs_per_percent / max_speed
    weight = round(selected_plant.max_weight * percent, 2)
    return weight


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


def num_slider_input(
    min_value: float,
    max_value: float,
    plant_name: str,
    key_type: str = "weight",
    a11y_label: str = "作物重量",
    unit: str = "kg",
    step: float = 0.01,
    format: str = "%.2f",
) -> float:
    default_value = max_value * 0.05

    slider_key = f"{key_type}-{plant_name}-slider"
    number_key = f"{key_type}-{plant_name}-number-input"
    current = st.session_state.get(slider_key, default_value)
    st.session_state[slider_key] = current
    st.session_state[number_key] = current

    col1, col2 = st.columns([7, 2])
    with col1:
        st.slider(
            a11y_label,
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=slider_key,
            on_change=lambda: st.session_state.update(
                {number_key: st.session_state[slider_key]}
            ),
            format=format,
            label_visibility="collapsed",
        )
    with col2:
        weight = st.number_input(
            a11y_label,
            min_value=min_value,
            max_value=max_value,
            step=step,
            key=number_key,
            on_change=lambda: st.session_state.update(
                {slider_key: st.session_state[number_key]}
            ),
            format=format,
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
    col1, col2 = st.columns([1, 1])
    with col1, st.container(horizontal=True):
        col_1, col_2 = st.columns([2, 3])

        plant_types = Plant.model_fields["type"].annotation.__args__
        with col_1:
            plant_type = st.selectbox(
                "选择类型", plant_types, label_visibility="collapsed"
            )

        # 提供作物选择
        plant_names = [
            p.name
            for p in sorted(
                (plant for plant in plants if plant.type == plant_type),
                key=lambda p: lazy_pinyin(p.name),
            )
        ]
        with col_2:
            plant_name = st.selectbox(
                "选择作物", plant_names, label_visibility="collapsed"
            )

        # 获取选择的植物对象
        selected_plant = next(plant for plant in plants if plant.name == plant_name)
        if selected_plant.type != "月球":
            base_mutation_names.remove("星空")
        st.image(
            f"https://www.fknc.top/carzyfarm/{plant_name}.png",
            width=48,
        )

    with col2, st.container(horizontal=True):
        st.write(
            f"""类型: {selected_plant.type}<br>
重量: {selected_plant.max_weight / 34:.2f}~{selected_plant.max_weight:.2f} kg""",
            unsafe_allow_html=True,
        )
        if selected_plant.growth_speed:
            st.write(f"速率: {selected_plant.growth_speed / 100:.1f} %/(秒·kg)")
        else:
            st.write("速率: 未知")

    speed_text = "速度"
    weight_text = "重量"
    percent_text = "百分比"

    disable_speed = selected_plant.growth_speed == 0
    with st.container(horizontal=True):
        selected_base_mutation_name = st.selectbox(
            "基础突变",
            ["无"] + base_mutation_names,
            format_func=display_name,
            label_visibility="collapsed",
        )
        input_approach = st.selectbox(
            "输入方式",
            [weight_text, percent_text]
            if disable_speed
            else [weight_text, speed_text, percent_text],
            label_visibility="collapsed",
            help="输入数据的方式",
        )
    if input_approach == weight_text:
        weight = input_by_weight(selected_plant)
    elif input_approach == speed_text:
        weight = input_by_speed(selected_plant)
    elif input_approach == percent_text:
        weight = input_by_percent(selected_plant)

    percent = weight / selected_plant.max_weight * 100
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.write(f"重量：{weight:.2f} kg")
    with col2:
        st.write(f"百分比：{percent:.1f}%")
    with col3:
        if selected_plant.growth_speed:
            secs_per_percent = selected_plant.growth_speed / 100 * weight
            st.write(f"生长时间：{time_format(secs_per_percent)}")
        else:
            st.write("生长时间：未知")

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
