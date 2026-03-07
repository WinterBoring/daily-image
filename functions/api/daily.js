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

  // 确定图片路径 (如果你配置了static为根目录，这样写是对的)
  const imagePath = format === "jpeg" 
    ? "/daily.jpeg" 
    : format === "original" 
      ? "/original.jpeg" 
      : "/daily.webp";

  // 构造目标 URL
  const imageUrl = new URL(request.url);
  imageUrl.pathname = imagePath;

  // 如果需要重定向
  if (redirect) {
    return Response.redirect(imageUrl.toString(), 302);
  }

  // 第一次请求：带 Request 对象，可命中 EdgeOne 缓存
  let originResponse = await fetch(new Request(imageUrl.toString(), request));

  // 第二次请求：直连 origin（兜底方案）
  if (!originResponse.ok) {
    originResponse = await fetch(imageUrl.toString());
    if (!originResponse.ok) {
      return new Response("Origin fetch failed", { status: 502 });
    }
  }

  // 🌟 核心修复：创建一个全新的 Headers 对象，彻底避免只读报错
  const newHeaders = new Headers(originResponse.headers);
  newHeaders.set("bing-cache", originResponse.redirected ? "BYPASS" : "EDGEONE");
  newHeaders.set("Cache-Control", "public, max-age=10800"); // 浏览器缓存 3 小时

  // 返回安全的响应
  return new Response(originResponse.body, {
    status: originResponse.status,
    statusText: originResponse.statusText,
    headers: newHeaders
  });
}
