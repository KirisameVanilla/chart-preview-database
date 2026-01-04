#!/usr/bin/env python3
"""
扫描 charts 目录中的图片文件，生成 previews.json 文件。
"""

import json
from pathlib import Path
from collections import defaultdict

# 支持的图片格式
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# GitHub 仓库信息
GITHUB_REPO_URL = "https://raw.githubusercontent.com/KirisameVanilla/chart-preview-database/refs/heads/main"


def parse_filename(filename: str) -> tuple[int, int] | None:
    """
    解析文件名，提取难度和序号。

    文件名格式：
    - 1.jpg, 2.jpg, ..., 5.jpg (难度 1-5，序号为 1)
    - 1_2.jpg (难度 1，序号为 2)
    - 1_3.jpg (难度 1，序号为 3)

    返回: (难度, 序号) 或 None
    """
    stem = Path(filename).stem  # 去掉扩展名

    # 尝试解析 "难度_序号" 格式
    if "_" in stem:
        parts = stem.split("_")
        if len(parts) == 2:
            try:
                difficulty = int(parts[0])
                sequence = int(parts[1])
                if 1 <= difficulty <= 5:
                    return (difficulty, sequence)
            except ValueError:
                pass
    else:
        # 尝试解析单个数字（难度）
        try:
            difficulty = int(stem)
            if 1 <= difficulty <= 5:
                return (difficulty, 1)  # 默认序号为 1
        except ValueError:
            pass

    return None


def scan_charts_directory(charts_dir: Path) -> dict:
    """
    扫描 charts 目录，生成预览图片的结构化数据。

    返回格式:
    {
        "id1": {
            "1": ["url1", "url2", ...],
            "2": [...],
            ...
            "5": [...]
        },
        ...
    }
    """
    result = {}

    # 遍历 charts 目录下的所有一级子目录
    if not charts_dir.exists():
        print(f"错误: {charts_dir} 目录不存在")
        return result

    for chart_dir in sorted(
        charts_dir.iterdir(), key=lambda p: int(p.name) if p.name.isdigit() else 0
    ):
        if not chart_dir.is_dir():
            continue

        chart_id = chart_dir.name

        # 初始化该 ID 的难度结构
        difficulties = {str(i): [] for i in range(1, 6)}

        # 临时存储：{难度: [(序号, 文件名), ...]}
        temp_storage = defaultdict(list)

        # 遍历该目录下的所有文件
        for file_path in chart_dir.iterdir():
            if not file_path.is_file():
                continue

            # 检查是否为图片文件
            if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            # 解析文件名
            parsed = parse_filename(file_path.name)
            if parsed is None:
                print(f"警告: 无法解析文件名 {file_path}")
                continue

            difficulty, sequence = parsed
            temp_storage[difficulty].append((sequence, file_path.name))

        # 按序号排序并生成 URL
        for difficulty, files in temp_storage.items():
            # 按序号排序
            files.sort(key=lambda x: x[0])

            # 生成 URL 列表
            urls = []
            for _, filename in files:
                url = f"{GITHUB_REPO_URL}/charts/{chart_id}/{filename}"
                urls.append(url)

            difficulties[str(difficulty)] = urls

        result[chart_id] = difficulties

    return result


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    charts_dir = project_root / "charts"
    output_file = project_root / "previews.json"

    print("开始扫描 charts 目录...")
    print(f"目录路径: {charts_dir}")

    # 扫描目录
    previews_data = scan_charts_directory(charts_dir)

    print(f"扫描完成，共找到 {len(previews_data)} 个图表目录")

    # 写入 JSON 文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(previews_data, f, ensure_ascii=False, indent=4)

    print(f"已生成 {output_file}")

    # 输出统计信息
    total_images = 0
    for chart_id, difficulties in previews_data.items():
        for difficulty, urls in difficulties.items():
            total_images += len(urls)

    print(f"总计图片数量: {total_images}")


if __name__ == "__main__":
    main()
