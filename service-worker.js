const CACHE = 'wx-v1';

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(['/wx-web/', '/wx-web/index.html']))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // metar_latest.json: ネット優先、失敗時は固定キーでキャッシュ返却
  if (url.pathname.endsWith('metar_latest.json')) {
    e.respondWith(
      fetch(e.request)
        .then(resp => {
          caches.open(CACHE).then(c => c.put(url.pathname, resp.clone()));
          return resp;
        })
        .catch(() => caches.match(url.pathname))
    );
    return;
  }

  // HTML: ネット優先、失敗時キャッシュ
  if (url.pathname.endsWith('.html') || url.pathname.endsWith('/wx-web/')) {
    e.respondWith(
      fetch(e.request)
        .then(resp => {
          caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
          return resp;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // 画像: キャッシュ優先（オフライン時は最後の画像を表示）
  if (e.request.destination === 'image') {
    e.respondWith(
      caches.match(e.request).then(cached => {
        const net = fetch(e.request).then(resp => {
          caches.open(CACHE).then(c => c.put(e.request, resp.clone()));
          return resp;
        });
        return cached || net;
      })
    );
    return;
  }

  // その他: ネット優先
  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
