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
        url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=15&n={n}&uhd=1&mkt=zh-CN"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        images = []
        for image in data["images"]:
            date = datetime.strptime(image["enddate"], "%Y%m%d").strftime("%Y-%m-%d")
            logging.info(f"获取到图片: {date}")
            # 生成高分辨率和备用URL
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
    """加载现有的index.json文件（兼容新旧格式）"""
    if not os.path.exists(INDEX_PATH):
        return []
    
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            logging.info("加载现有index.json成功")
            data = json.load(f)
            # 如果是带有 images 字段的新格式，提取列表；如果是旧格式的纯数组，直接返回
            return data.get("images", data) if isinstance(data, dict) else data
    except Exception as e:
        logging.error(f"加载现有index.json失败: {e}")
        return []

def save_image(img, filepath):
    """保存图片到指定路径，并确保父目录存在"""
    try:
        # 确保按月分类的子目录存在
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
    """合并新图片并按月分类保存，保留12个月"""
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
            
        month_str = date[:7] # 获取 YYYY-MM
        filename = f"{date}.webp"
        
        # 物理路径保存到月份文件夹
        filepath = os.path.join(PICTURE_FOLDER, month_str, filename)
        # 相对路径用于前端访问
        relative_path = f"/picture/{month_str}/{filename}"
        
        img = download_image(img_info["url"])
        if img is None:
            continue
            
        if not save_image(img, filepath):
            continue
            
        # 如果是今天的图，在根目录额外保存几份作为预览和兼容
        if date == today_str:
            logging.info("保存今天的图片为 daily.webp / daily.jpeg / original.jpeg")
            save_image(img, os.path.join(STATIC_FOLDER, "daily.webp"))
            img.save(os.path.join(STATIC_FOLDER, "daily.jpeg"), "JPEG", quality=95, optimize=True)
            img.save(os.path.join(STATIC_FOLDER, "original.jpeg"), "JPEG", quality=100)
            
        updated_index.append({
            "filename": filename,
            "date": date,
            "month": month_str, # 写入月份，方便前端直接过滤
            "path": relative_path,
            "copyright": img_info.get("copyright", ""),
            "url": img_info.get("url", "")
        })
    
    # 合并现有和新数据并按日期排序
    combined_index = existing_index + updated_index
    combined_index.sort(key=lambda x: x["date"], reverse=True)
    
    # 保留最近12个月（约365天）的数据
    cutoff_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    filtered_index = []
    
    for item in combined_index:
        if item["date"] > cutoff_date:
            filtered_index.append(item)
        else:
            # 读取 path 并定位物理文件
            # 兼容老数据（如果老数据path不带月份，也会正确处理）
            path_to_remove = item.get("path", f"/picture/{item['filename']}")
            filepath_to_remove = os.path.join(STATIC_FOLDER, path_to_remove.lstrip('/'))
            
            try:
                if os.path.exists(filepath_to_remove):
                    os.remove(filepath_to_remove)
                    logging.info(f"删除超过12个月的旧图片: {filepath_to_remove}")
                    
                    # 尝试清理空的月份文件夹
                    month_dir = os.path.dirname(filepath_to_remove)
                    if os.path.exists(month_dir) and not os.listdir(month_dir):
                        os.rmdir(month_dir)
                        logging.info(f"清理空目录: {month_dir}")
            except Exception as e:
                logging.error(f"删除旧图片失败 {filepath_to_remove}: {e}")
    
    return filtered_index

def update_index(index_list):
    """更新index.json文件，包含月份清单和具体图片数据"""
    try:
        # 生成可用月份列表（去重并按倒序排列）
        months = sorted(list(set(item.get("month", item["date"][:7]) for item in index_list)), reverse=True)
        
        data_to_save = {
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "months": months,
            "images": index_list
        }
        
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        logging.info(f"已更新 index.json，共 {len(index_list)} 项图片，覆盖 {len(months)} 个月")
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
