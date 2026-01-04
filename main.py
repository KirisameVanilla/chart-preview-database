import requests
import os
from pathlib import Path


def download_image(url, save_path):
    """下载图片到指定路径"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False


def get_unique_filename(directory, base_name, extension):
    """生成唯一文件名，如果文件已存在则添加_i后缀"""
    file_path = directory / f"{base_name}{extension}"

    if not file_path.exists():
        return file_path

    # 文件已存在，添加_i后缀
    i = 2
    while True:
        file_path = directory / f"{base_name}_{i}{extension}"
        if not file_path.exists():
            return file_path
        i += 1


def main():
    # 难度映射
    difficulty_mapping = {"easy": 1, "normal": 2, "hard": 3, "oni": 4, "ura": 5}

    # 创建基础目录
    base_dir = Path("charts")
    base_dir.mkdir(exist_ok=True)

    # 1. 从API获取song list
    print("Fetching song list from API...")
    try:
        response = requests.get("https://taiko.wiki/api/song", timeout=30)
        response.raise_for_status()
        songs = response.json()
        print(f"Found {len(songs)} songs")
    except Exception as e:
        print(f"Failed to fetch song list: {e}")
        return

    # 2. 遍历每首歌曲
    for song in songs:
        # 获取songNo作为文件夹名
        song_no = song.get("songNo")
        if not song_no:
            print("Warning: Song without songNo, skipping...")
            continue

        # 创建歌曲文件夹
        song_dir = base_dir / str(song_no)
        song_dir.mkdir(exist_ok=True)
        print(f"\nProcessing song {song_no}...")

        # 3. 获取courses字段
        courses = song.get("courses", {})

        # 4. 遍历难度映射
        for difficulty_key, difficulty_value in difficulty_mapping.items():
            if difficulty_key in courses:
                course_data = courses[difficulty_key]
                images = course_data.get("images", [])

                print(f"  Found {len(images)} images for {difficulty_key}")

                # 5. 下载每个图片
                for image_url in images:
                    if not image_url:
                        continue

                    # 获取文件扩展名
                    try:
                        # 从URL中提取扩展名
                        url_path = image_url.split("?")[0]  # 去掉查询参数
                        extension = os.path.splitext(url_path)[1] or ".jpg"
                    except:
                        extension = ".jpg"

                    # 生成唯一文件名
                    save_path = get_unique_filename(
                        song_dir, str(difficulty_value), extension
                    )

                    # 下载图片
                    download_image(image_url, save_path)

    print("\nDownload completed!")


if __name__ == "__main__":
    main()
