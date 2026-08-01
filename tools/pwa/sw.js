// Shell cache, so composing works with no connection. Bump SHELL when any
// cached file changes, or phones will keep serving the old one.
const SHELL = "records-shell-v1";
const FILES = ["./", "index.html", "app.js", "record.js", "forge.js", "manifest.webmanifest", "icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  // The forge API is someone else's origin and must never be served from cache.
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  event.respondWith(
    caches.match(request).then((hit) => hit || fetch(request).catch(() => caches.match("index.html"))),
  );
});
