import requests
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading


# 为imgur设置速率限制
imgur_lock = threading.Lock()
imgur_last_request_time = 0
IMGUR_MIN_INTERVAL = 2  # imgur请求之间的最小间隔（秒）

# 全局统计信息
stats_lock = threading.Lock()
failed_downloads = []  # 记录失败的下载 (url, reason)


def download_image(url, save_path):
    """下载图片到指定路径，支持重试机制"""
    max_retries = 3
    retry_delay = 2  # 初始重试延迟（秒）

    for attempt in range(max_retries):
        try:
            # 如果是imgur链接，需要限速
            if "i.imgur.com" in url:
                global imgur_last_request_time
                with imgur_lock:
                    current_time = time.time()
                    time_since_last = current_time - imgur_last_request_time
                    if time_since_last < IMGUR_MIN_INTERVAL:
                        sleep_time = IMGUR_MIN_INTERVAL - time_since_last
                        time.sleep(sleep_time)
                    imgur_last_request_time = time.time()

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(save_path, "wb") as f:
                f.write(response.content)
            return True, None

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # 指数退避
                    time.sleep(wait_time)
                    continue
                else:
                    return False, f"429 Too Many Requests after {max_retries} attempts"
            else:
                return False, f"HTTP Error {e.response.status_code}: {str(e)}"
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)
                time.sleep(wait_time)
                continue
            else:
                return False, f"{type(e).__name__}: {str(e)}"

    return False, "Unknown error"


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


def process_song(song, base_dir, difficulty_mapping):
    """处理单个歌曲的下载任务"""
    # 获取songNo作为文件夹名
    song_no = song.get("songNo")
    if not song_no:
        return {"success": 0, "failed": 0, "skipped": 1}

    # 创建歌曲文件夹
    song_dir = base_dir / str(song_no)
    song_dir.mkdir(exist_ok=True)

    # 获取courses字段
    courses = song.get("courses", {})

    success_count = 0
    failed_count = 0

    # 遍历难度映射
    for difficulty_key, difficulty_value in difficulty_mapping.items():
        if difficulty_key in courses:
            course_data = courses[difficulty_key]
            if course_data is None:
                continue
            images = course_data.get("images", [])

            # 下载每个图片
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
                success, error = download_image(image_url, save_path)
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    with stats_lock:
                        failed_downloads.append(
                            {"song_no": song_no, "url": image_url, "reason": error}
                        )

    return {"success": success_count, "failed": failed_count, "skipped": 0}


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
        print(f"Found {len(songs)} songs\n")
    except Exception as e:
        print(f"Failed to fetch song list: {e}")
        return

    # 2. 使用多线程处理歌曲下载
    max_workers = 5  # 同时下载的歌曲数量
    total_success = 0
    total_failed = 0
    total_skipped = 0
    completed_songs = 0

    print(f"Starting parallel download with {max_workers} workers...\n")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_song = {
            executor.submit(process_song, song, base_dir, difficulty_mapping): song
            for song in songs
        }

        # 等待任务完成
        for future in as_completed(future_to_song):
            song = future_to_song[future]
            try:
                result = future.result()
                total_success += result["success"]
                total_failed += result["failed"]
                total_skipped += result["skipped"]
                completed_songs += 1

                # 显示进度
                print(
                    f"\rProgress: {completed_songs}/{len(songs)} songs processed",
                    end="",
                    flush=True,
                )

            except Exception as e:
                song_no = song.get("songNo", "unknown")
                total_skipped += 1
                completed_songs += 1
                with stats_lock:
                    failed_downloads.append(
                        {
                            "song_no": song_no,
                            "url": "N/A",
                            "reason": f"Song processing error: {str(e)}",
                        }
                    )

    # 下载完成后输出统计信息
    print("\n\n" + "=" * 60)
    print("下载完成！")
    print("=" * 60)
    print(f"✓ 成功下载: {total_success} 张图片")
    print(f"✗ 下载失败: {total_failed} 张图片")
    if total_skipped > 0:
        print(f"⊘ 跳过歌曲: {total_skipped} 首")

    # 输出失败详情
    if failed_downloads:
        print("\n" + "-" * 60)
        print("失败详情:")
        print("-" * 60)
        for idx, failure in enumerate(failed_downloads, 1):
            print(f"\n{idx}. 歌曲编号: {failure['song_no']}")
            print(f"   URL: {failure['url']}")
            print(f"   原因: {failure['reason']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
