#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def extract_code_blocks(input_file, output_file):
    """
    从输入文件中提取包含特定关键词的代码块并保存到输出文件

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
    """

    # 读取整个文件内容
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 要搜索的关键词
    keywords = ['name:"土豆"', 'name:"颤栗"']
    extracted_blocks = []

    for keyword in keywords:
        block = extract_block_for_keyword(content, keyword)
        if block:
            extracted_blocks.append(block)

    plants, mutations = extracted_blocks
    with open(output_file, "w", encoding="utf-8") as f:
        # 清空文件并写入新内容
        f.write("// Extracted code blocks\n\n")

        f.write("const plants = ")
        f.write(plants)
        f.write(";\n")

        f.write("const mutations = ")
        f.write(mutations)
        f.write(";\n")

        f.write("""
const fs = require('fs').promises;
async function exportToJson() {
  try {
    await fs.writeFile('src/fknc_calc/plants.json', JSON.stringify(plants, null, 2));
    await fs.writeFile('src/fknc_calc/mutations.json', JSON.stringify(mutations, null, 2));
  } catch (error) {
    console.error('写入文件失败:', error);
  }
}

exportToJson();
""")


def extract_block_for_keyword(content: str, keyword):
    """
    为特定关键词提取代码块

    Args:
        content: 文件内容字符串
        keyword: 要搜索的关键词

    Returns:
        提取的代码块字符串，如果没找到则返回None
    """

    # 找到关键词的位置
    keyword_pos = content.find(keyword)
    if keyword_pos == -1:
        print(f"警告: 未找到包含 '{keyword}' 的内容")
        return None

    start_pos = content.rfind("[{", 0, keyword_pos)
    if start_pos == -1:
        print(f"错误: 在关键词 '{keyword}' 之前未找到 '['")
        return None

    end_pos = content.find("}]", start_pos, len(content))

    if end_pos == -1:
        print("错误: 未找到匹配的 '}]'")
        return None

    # 提取代码块
    extracted_block = content[start_pos : end_pos + 2]
    return extracted_block


def main():
    """主函数"""
    input_file = "index.js"  # 输入文件名
    output_file = "export.js"  # 输出文件名

    try:
        extract_code_blocks(input_file, output_file)
    except FileNotFoundError:
        print(f"错误: 找不到输入文件 '{input_file}'")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
