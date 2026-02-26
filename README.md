# 🌅 Daily Bing Image 自动更新项目

<p align="center">
  <img src="https://raw.githubusercontent.com/WinterBoring/daily-image/refs/heads/page/daily.webp" alt="Daily Bing Wallpaper" width="600" />
</p>

这是一个基于 GitHub Actions 自动获取并展示 Bing 每日高清壁纸的项目。每天早上 6 点（中国时间）自动抓取最新壁纸，生成 WebP/JPEG 格式图片，维护12个月内的壁纸，并发布至 `page` 分支，用于 Pages 服务部署并展示。

**推荐使用 EO Pages 服务部署，目前已支持随机图 API 功能。**

---

## ✨ 功能亮点

- 📅 **每日自动更新**：每天定时从 Bing 官方源抓取高清壁纸（2560x1600 或 1920x1080）。
- 🖼️ **多格式保存**：保存为 `webp`, `jpeg` 等格式，兼顾网页加载与高清查看。
- 📂 **历史记录管理**：维护12个月内的壁纸按月保存及信息索引 `index.json`。
- 🌐 **网页展示支持**：与 EO Pages 搭配，展示壁纸和版权信息。

---

## 📦 文件结构

```
.
├── static/
│   ├── daily.webp            # 今日壁纸（WebP 格式，用于网页展示）
│   ├── daily.jpeg            # 今日壁纸（JPEG 压缩版）
│   ├── original.jpeg         # 今日壁纸（原图最高画质）
│   └── picture/
│       ├── index.json        # 🌟 更新：包含 months 列表和详细信息的 JSON 索引
│       ├── 2026-02/          # 🌟 新增：按月份生成的独立子文件夹
│       │   ├── 2026-02-25.webp
│       │   └── 2026-02-24.webp
│       └── 2026-01/          # 🌟 新增：历史月份文件夹（保留最近 12 个月）
│           └── 2026-01-31.webp
├── page/                     # （前端静态文件存放区）
│   ├── index.html            # 🌟 更新：新增了下拉月份选择器的前端模板
│   └── favicon.ico           # 🌟 更新：网站图标
├── api/                      # 🌟 新增：EdgeOne 边缘函数目录
│   ├── random.js             # 随机图片 API (已兼容新版按月 JSON)
│   ├── daily.js              # 今日图片 API (已修复 Headers 报错)
│   └── index.js              # API 导航页
├── edgeone.json              # 🌟 新增：EdgeOne 路由、缓存与跨域配置 (已修复路径规则)
├── main.py                   # 🌟 更新：按月分类、12个月清理逻辑的主 Python 脚本
└── .github/workflows/
    └── bing-image.yml        # GitHub Actions 定时任务配置 (保持不变)
```

---

## ⏱️ 自动化逻辑

通过 GitHub Actions 实现每日定时更新：

- 使用 `cron: '0 22 * * *'`（UTC 时间），即北京时间早上 6 点。
- 运行 `main.py` 获取并保存壁纸。
- 将图片和网页内容推送到 `page` 分支。
- 使用 GitHub Pages 公开展示（`https://github.com/WinterBoring/daily-image/`）。

---

## 🌍 在线预览地址

- 🔗 **LiuShen**：[https://bing.liushen.fun/](https://bing.liushen.fun/)
- 🔗 **WinterBoring**：[https://bing.bluelife.dpdns.org/](https://bing.bluelife.dpdns.org/)

---

## 🛺 使用方式

1. **随机图 API**：
   - 访问 `https://bing.bluelife.dpdns.org/api/random` 获取随机壁纸(365天随机)。
   - 可在网页中直接使用，如：`<img src="https://bing.bluelife.dpdns.org/api/random" alt="随机壁纸" />`。

2. **每日一图 API**：
   - 访问 `https://bing.bluelife.dpdns.org/api/daily` 或者 `https://bing.bluelife.dpdns.org/daily.webp` 获取今日壁纸。
   - 可在网页中直接使用，如：`<img src="https://bing.bluelife.dpdns.org/api/daily" alt="今日壁纸" />`。

更多参数欢迎访问地址：[https://bing.bluelife.dpdns.org/api](https://bing.bluelife.dpdns.org/api) 进行查询。

## 📜 License

本项目使用 MIT License 开源，壁纸版权归 Bing 及原作者所有，仅供学习与个人使用，严禁商用。

---

## 🤝 致谢

- [LiuShen](https://github.com/willow-god/daily-image/)
- 微软 Bing 壁纸源
- GitHub Actions 自动化平台
