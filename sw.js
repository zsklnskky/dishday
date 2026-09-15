// Минимальный service worker Dishday.
// network-first для HTML (чтобы люди сразу видели обновления онлайн),
// cache-first для статики (фото с ?v=хэш), stale-while-revalidate для prices/*.json (обновляет GitHub Actions),
// Apps Script (оплата, лист ожидания) не трогаем никогда.
const CACHE = "dishday-v3";
const PRECACHE_URLS = [
  "./",
  "./app/",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/icon-maskable-192.png",
  "./icons/icon-maskable-512.png",
  "./icons/apple-touch-icon.png",
  "./favicon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE_URLS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // никогда не кэшировать и не перехватывать запросы к Google Apps Script
  if (url.hostname.endsWith("script.google.com") || url.hostname.endsWith("googleusercontent.com")) {
    return;
  }
  if (req.method !== "GET" || url.origin !== self.location.origin) return;

  const isHTML = req.mode === "navigate" || (req.headers.get("accept") || "").includes("text/html");

  if (isHTML) {
    event.respondWith(
      // no-store: мимо HTTP-кэша браузера, иначе после смены страницы люди видят старую (например старый редирект)
      fetch(req.url, { cache: "no-store", credentials: "same-origin" })
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req.url, copy));
          return res;
        })
        .catch(() => caches.match(req.url))
    );
    return;
  }

  if (url.pathname.includes("/prices/")) {
    // отдаём кэш сразу, свежую версию тянем в фоне к следующему открытию
    const fresh = fetch(req).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
      return res;
    });
    event.waitUntil(fresh.catch(() => {}));
    event.respondWith(caches.match(req).then((cached) => cached || fresh));
    return;
  }

  event.respondWith(
    caches.match(req).then(
      (cached) =>
        cached ||
        fetch(req).then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); }
          return res;
        })
    )
  );
});
