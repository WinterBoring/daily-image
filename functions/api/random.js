export default async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  // 从当前请求的域名拼接 JSON 地址
  const host = url.origin;
  const jsonUrl = `${host}/picture/index.json`;

  // 直接 fetch JSON（EO 会自己命中缓存）
  const fetchResp = await fetch(new Request(jsonUrl, request));
  if (!fetchResp.ok) {
    return new Response("Failed to load index.json", { status: 502 });
  }

  // 接收原始数据
  let data = await fetchResp.json();

  // 🌟 核心修改点：兼容新版对象格式和老版数组格式
  let images = Array.isArray(data) ? data : (data.images || []);

  if (images.length === 0) {
    return new Response("No images found in index", { status: 404 });
  }

  // 去掉最后一张，防止过期
  if (images.length > 1) {
    images = images.slice(0, -1);
  }

  // 随机挑一张
  const randomImage = images[Math.floor(Math.random() * images.length)];
  const redirect = url.searchParams.get("redirect") === "true";

  const imagePath = randomImage.path; // e.g. /picture/2026-02/2026-02-25.webp
  const imageUrl = new URL(imagePath, request.url);

  if (redirect) {
    // 🚀 302 跳转 (建议转为完整的 URL 字符串)
    return Response.redirect(imageUrl.toString(), 302);
  }

  // 🖼 直接返回图片二进制，走 EO 节点缓存
  const resp = await fetch(new Request(imageUrl.toString(), request));
  if (!resp.ok) {
    return new Response("Failed to fetch image", { status: 502 });
  }

  return new Response(resp.body, {
    headers: {
      "Content-Type": resp.headers.get("Content-Type") || "image/webp",
      "Cache-Control": "public, max-age=10800", // 浏览器缓存 3 小时
      "bing-cache": "EO-FETCH", // 标识 EO fetch 命中
    },
  });
}
