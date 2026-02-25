import os
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
import json
import logging

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 路径配置
STATIC_FOLDER = "static"
PICTURE_FOLDER = os.path.join(STATIC_FOLDER, "picture")
DAILY_IMAGE_PATH = os.path.join(STATIC_FOLDER, "daily.webp")
INDEX_PATH = os.path.join(PICTURE_FOLDER, "index.json")

# 确保文件夹存在
os.makedirs(PICTURE_FOLDER, exist_ok=True)

def fetch_bing_images(n=8):
    """获取最新的Bing壁纸信息"""
    try:
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n={n}&uhd=1&mkt=zh-CN"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        images = []
        for image in data["images"]:
            date = datetime.strptime(image["enddate"], "%Y%m%d").strftime("%Y-%m-%d")
            logging.info(f"获取到图片: {date}")
            urlbase = image["urlbase"]
            high_res_url = f"https://www.bing.com{urlbase}_UHD.jpg"
            fallback_url = f"https://www.bing.com{urlbase}_1920x1080.jpg"

            test_resp = requests.head(high_res_url)
            image_url = high_res_url if test_resp.status_code == 200 else fallback_url

            images.append({
                "date": date,
                "url": image_url,
                "copyright": image.get("copyright", ""),
                "urlbase": urlbase
            })

        return images
    except Exception as e:
        logging.error(f"获取 Bing 图片信息失败: {e}")
        return []

def download_image(url):
    """下载图片并返回PIL Image对象"""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception as e:
        logging.error(f"下载图片失败: {e}")
        return None

def load_existing_index():
    """加载现有的index.json文件"""
    if not os.path.exists(INDEX_PATH):
        return []
    
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            logging.info("加载现有index.json成功")
            return json.load(f)
    except Exception as e:
        logging.error(f"加载现有index.json失败: {e}")
        return []

def save_image(img, filepath):
    """保存图片到指定路径"""
    try:
        # 确保图片所在的子目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # 限制最大尺寸
        max_width, max_height = 2560, 1600
        img.thumbnail((max_width, max_height))
        img.save(filepath, "WEBP", quality=80, method=6)
        logging.info(f"保存图片 {filepath}")
        return True
    except Exception as e:
        logging.error(f"保存图片失败 {filepath}: {e}")
        return False

def merge_and_update_images(new_images, existing_index):
    """合并新图片和现有索引，并按月份保存文件"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"今天的日期: {today_str}")
    updated_index = []
    existing_dates = {item["date"] for item in existing_index}
    
    # 处理新图片
    for img_info in new_images:
        date = img_info["date"]
        logging.info(f"处理图片: {date}")
        if date in existing_dates:
            logging.info(f"图片 {date} 已存在，跳过")
            continue
            
        # --- 修改点：按月份创建文件夹路径 ---
        month_str = date[:7]  # 获取 YYYY-MM
        filename = f"{date}.webp"
        # 实际存储路径：static/picture/2026-02/2026-02-25.webp
        filepath = os.path.join(PICTURE_FOLDER, month_str, filename)
        # 存入 index.json 的访问路径：/picture/2026-02/2026-02-25.webp
        relative_path = f"/picture/{month_str}/{filename}"
        
        img = download_image(img_info["url"])
        if img is None:
            continue
            
        if not save_image(img, filepath):
            continue
            
        # 如果是今天的图，保存到 static 根目录供直接引用
        if date == today_str:
            logging.info("保存今日预览图: daily.webp / daily.jpeg")
            save_image(img, os.path.join(STATIC_FOLDER, "daily.webp"))
            img.save(os.path.join(STATIC_FOLDER, "daily.jpeg"), "JPEG", quality=95, optimize=True)
            img.save(os.path.join(STATIC_FOLDER, "original.jpeg"), "JPEG", quality=100)
            
        updated_index.append({
            "filename": filename,
            "date": date,
            "path": relative_path,
            "copyright": img_info.get("copyright", ""),
            "url": img_info.get("url", "")
        })
    
    # 合并数据并排序
    combined_index = existing_index + updated_index
    combined_index.sort(key=lambda x: x["date"], reverse=True)
    
    # 保留最近90天的数据
    cutoff_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    filtered_index = []
    
    for item in combined_index:
        if item["date"] > cutoff_date:
            filtered_index.append(item)
        else:
            # --- 修改点：根据 path 字段还原物理路径进行删除 ---
            # item["path"] 类似于 "/picture/2026-01/2026-01-01.webp"
            # 去掉开头的 / 并与 static 目录拼接
            filepath = os.path.join(STATIC_FOLDER, item["path"].lstrip('/'))
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logging.info(f"物理删除过期图片: {filepath}")
                    
                    # 可选：尝试删除空的月份文件夹
                    month_dir = os.path.dirname(filepath)
                    if not os.listdir(month_dir):
                        os.rmdir(month_dir)
                        logging.info(f"删除空目录: {month_dir}")
            except Exception as e:
                logging.error(f"删除旧图片失败 {filepath}: {e}")
    
    return filtered_index

def update_index(index_list):
    """更新index.json文件"""
    try:
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(index_list, f, ensure_ascii=False, indent=2)
        logging.info(f"已更新 index.json，共 {len(index_list)} 项")
    except Exception as e:
        logging.error(f"更新index.json失败: {e}")

def main():
    logging.info("开始获取 Bing 图片...")
    existing_index = load_existing_index()
    new_images = fetch_bing_images(8)

    if not new_images:
        logging.error("未获取到任何新图像信息")
        return

    updated_index = merge_and_update_images(new_images, existing_index)
    update_index(updated_index)

if __name__ == "__main__":
    main()
