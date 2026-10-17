export default async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  // 从当前请求的域名拼接 JSON 地址
  const host = url.origin;
  const jsonUrl = `${host}/picture/index.json`;

  // 直接 fetch JSON
  const fetchResp = await fetch(new Request(jsonUrl, request));
  if (!fetchResp.ok) {
    return new Response("Failed to load index.json", { status: 502 });
  }

  // 接收原始数据
  let data = await fetchResp.json();

  // 🌟【修改点 1】：兼容新旧格式并提取图片列表
  let images = Array.isArray(data) ? data : (data.images || []);

  // 🌟【修改点 2】：新增核心逻辑 - 仅在“最新月份”里提取随机图
  // 判断依据：如果 data 含有 months 数组，则取第一个月份作为过滤条件
  if (!Array.isArray(data) && data.months && data.months.length > 0) {
    const latestMonth = data.months[0]; // 获取最新月份，如 "2026-03"
    images = images.filter(img => 
      (img.month === latestMonth) || (img.date && img.date.startsWith(latestMonth))
    );
  }

  if (images.length === 0) {
    return new Response("No images found in index", { status: 404 });
  }

  // 🌟【修改点 3】：移除“去掉最后一张”的逻辑
  // 因为现在只在最新月提取，数据都是新鲜的，没必要人为减少样本量
  
  // 随机挑一张
  const randomImage = images[Math.floor(Math.random() * images.length)];
  const redirect = url.searchParams.get("redirect") === "true";

  const imagePath = randomImage.path; 
  const imageUrl = new URL(imagePath, request.url);

  if (redirect) {
    // 🌟【修改点 4】：在重定向 URL 后添加随机时间戳
    // 解决浏览器因 URL 固定而直接读取本地缓存导致“刷新不更换”的问题
    imageUrl.searchParams.set('t', Date.now()); 
    
    // 🚀 302 跳转
    return Response.redirect(imageUrl.toString(), 302);
  }

  // 🖼 直接返回图片二进制
  const resp = await fetch(new Request(imageUrl.toString(), request));
  if (!resp.ok) {
    return new Response("Failed to fetch image", { status: 502 });
  }

  return new Response(resp.body, {
    headers: {
      "Content-Type": resp.headers.get("Content-Type") || "image/webp",
      "Cache-Control": "public, max-age=10800", 
      "bing-cache": "EO-FETCH",
      // 🌟【修改点 5】：增加跨域支持，方便其他页面调用
      "Access-Control-Allow-Origin": "*",
    },
  });
}
