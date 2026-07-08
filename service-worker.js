const CACHE = 'wx-v2';
const CORE = ['./', './index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 動的画像URLを正規化してキャッシュキーにする
//  例) jpn_b13_0610.jpg              -> jpn_b13_TS.jpg
//      WANLF129_RJTD_20260707060000.PNG -> WANLF129_RJTD_TS.PNG
//      2d256nradar_202607071406.jpg  -> 2d256nradar_TS.jpg
//  クエリ(?_=…)も除去。固定URL(aupa20_00.gif 等)は変化しない。
function imgKey(url) {
  return url.split('?')[0].replace(/_(\d{4,14})(\.\w+)$/i, '_TS$2');
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // metar_latest.json: ネット優先、失敗時は固定キーでキャッシュ返却
  if (url.pathname.endsWith('metar_latest.json')) {
    e.respondWith(
      fetch(req)
        .then(resp => {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(url.pathname, clone));
          return resp;
        })
        .catch(() => caches.match(url.pathname))
    );
    return;
  }

  // ページ本体(ナビゲーション/HTML): ネット優先、オフライン時 index.html
  if (req.mode === 'navigate' ||
      url.pathname.endsWith('.html') ||
      url.pathname.endsWith('/wx-web/')) {
    e.respondWith(
      fetch(req)
        .then(resp => {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put('./index.html', clone));
          return resp;
        })
        .catch(() =>
          caches.match('./index.html').then(r => r || caches.match('./'))
        )
    );
    return;
  }

  // 画像: stale-while-revalidate（正規化キーでオフライン時も直近画像を表示）
  if (req.destination === 'image') {
    const key = imgKey(req.url);
    e.respondWith(
      caches.match(key).then(cached => {
        const net = fetch(req).then(resp => {
          if (resp && (resp.ok || resp.type === 'opaque')) {
            const clone = resp.clone();
            caches.open(CACHE).then(c => c.put(key, clone));
          }
          return resp;
        }).catch(() => cached);
        return cached || net;
      })
    );
    return;
  }

  // その他: ネット優先、失敗時キャッシュ
  e.respondWith(fetch(req).catch(() => caches.match(req)));
});
