const CACHE_NAME = "family-pandit-shell-v3";
const CACHE_PREFIX = "family-pandit-shell-";
const APP_SHELL = ["/", "/manifest.webmanifest", "/icons/panditji.svg", "/privacy", "/terms"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
        .map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  // Never cache user questions, personal data or API responses.
  if (url.pathname.startsWith("/api/") || url.pathname === "/ready" || url.pathname === "/health") return;

  if (request.mode === "navigate") {
    event.respondWith(fetch(request).then(async response => {
      if (response.ok) {
        const copy = response.clone();
        const cache = await caches.open(CACHE_NAME);
        await cache.put(request, copy);
        if (url.pathname !== "/") await cache.put("/", response.clone());
      }
      return response;
    }).catch(async () => {
      const cache = await caches.open(CACHE_NAME);
      return (await cache.match(request)) || (await cache.match("/"));
    }));
    return;
  }

  event.respondWith(caches.match(request).then(cached => cached || fetch(request)));
});
