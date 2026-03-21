export default async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  // 处理参数
  const format = url.searchParams.get("format") || "webp";
  const redirect = url.searchParams.get("redirect") === "true";

  // 验证参数
  const allowedFormats = ["webp", "jpeg", "original"];
  if (!allowedFormats.includes(format)) {
    return new Response("Invalid format parameter", { status: 400 });
  }

  // 确定图片路径
  const imagePath = format === "jpeg" 
    ? "/daily.jpeg" 
    : format === "original" 
      ? "/original.jpeg" 
      : "/daily.webp";

  // 构造目标 URL
  const imageUrl = new URL(imagePath, request.url);

  // 🌟【修改点 1】：为目标 URL 注入时间戳参数
  // 作用：强制穿透 CDN 节点或浏览器可能存在的陈旧缓存，确保获取的是 Actions 最新生成的图片
  imageUrl.searchParams.set('t', Date.now());

  // 如果需要重定向
  if (redirect) {
    // 🌟【修改点 2】：302 重定向时携带时间戳
    // 解决浏览器因 URL 固定而直接读取本地磁盘缓存导致图片不更新的问题
    return Response.redirect(imageUrl.toString(), 302);
  }

  // 尝试从缓存或源站获取
  let originResponse = await fetch(new Request(imageUrl.toString(), request));

  if (!originResponse.ok) {
    originResponse = await fetch(imageUrl.toString());
    if (!originResponse.ok) {
      return new Response("Origin fetch failed", { status: 502 });
    }
  }

  // 创建全新的 Headers 对象
  const newHeaders = new Headers(originResponse.headers);
  
  // 🌟【修改点 3】：添加跨域访问支持
  // 允许你的 API 被其他站点（如个人博客）直接调用作为背景
  newHeaders.set("Access-Control-Allow-Origin", "*");
  
  newHeaders.set("bing-cache", originResponse.redirected ? "BYPASS" : "EDGEONE");
  newHeaders.set("Cache-Control", "public, max-age=10800"); // 浏览器缓存 3 小时

  // 返回安全的响应
  return new Response(originResponse.body, {
    status: originResponse.status,
    statusText: originResponse.statusText,
    headers: newHeaders
  });
}
