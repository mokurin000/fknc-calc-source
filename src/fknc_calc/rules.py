from fknc_calc import Plant

__all__ = ["is_mutation_disabled"]

# 配方数据：每种突变产物所需的原料
RECIPES = [
    {"ingredients": ["潮湿", "结霜"], "result": "冰冻"},
    {"ingredients": ["太阳耀斑", "灼热"], "result": "流火"},
    {"ingredients": ["沙尘", "潮湿"], "result": "陶化"},
    {"ingredients": ["陶化", "灼热"], "result": "瓷化"},
]

MOON_ONLY = ["流火", "日蚀", "暗雾", "陨石"]


def get_all_ingredients(mutation: str, visited: set[str] | None = None) -> list[str]:
    """
    递归获取某个突变项的所有原料（包括直接和间接原料）

    Args:
        mutation: 要查询的突变项名称
        visited: 已访问过的突变集合，用于防止循环引用

    Returns:
        所有原料的名称列表
    """
    if visited is None:
        visited = set()

    if mutation in visited:
        return []

    visited.add(mutation)
    all_ingredients = []

    for recipe in RECIPES:
        if recipe["result"] == mutation:
            # 加入直接原料
            all_ingredients.extend(recipe["ingredients"])
            # 递归获取每个原料的原料
            for ingredient in recipe["ingredients"]:
                all_ingredients.extend(get_all_ingredients(ingredient, visited))

    return all_ingredients


def is_mutation_disabled(
    selected_mutations: list[str],
    plant: Plant,
    new_mutation: str,
) -> bool:
    """
    判断新突变在当前已选中的突变列表中是否应该被禁用

    Args:
        selected_mutations: 当前已选中的突变列表
        plant: 当前已选中的植物
        new_mutation: 要检查的新突变名称

    Returns:
        True表示禁用（不可选择），False表示可用（可选择）
    """
    if new_mutation == "潮湿":
        return False

    # 非月球果实无法获得月球突变
    if plant.type != "月球" and new_mutation in MOON_ONLY:
        return True

    if new_mutation == "灼热":
        has_flow_fire = "流火" in selected_mutations
        has_porcelain = "瓷化" in selected_mutations
        return has_flow_fire and has_porcelain

    if new_mutation == "沙尘" and "潮湿" in selected_mutations:
        return "陶化" in selected_mutations or "瓷化" in selected_mutations

    # 通用规则：检查配方链的互斥关系
    # 如果已选中某个产物，那么它的所有原料都不能再被选中
    for recipe in RECIPES:
        if recipe["result"] in selected_mutations:
            # 获取该产物的所有原料（过滤掉永不禁用的"潮湿"）
            all_ingredients = [
                ing for ing in get_all_ingredients(recipe["result"]) if ing != "潮湿"
            ]
            # 如果新突变是这些原料之一，则禁用
            if new_mutation in all_ingredients:
                return True

    return False


def is_mutation_allowed(
    selected_mutations: list[str],
    plant: Plant,
    new_mutation: str,
) -> bool:
    return not is_mutation_disabled(selected_mutations, plant, new_mutation)
