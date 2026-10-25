const CACHE = 'wx-v3';
const CORE = ['./', './index.html'];
const NET_TIMEOUT_MS = 15000;   // DWD など遅いサーバでも網羅できる長さ

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

// 動的画像URLを正規化してキャッシュキーにする（オフライン時に「直近の1枚」を返すため）
//  例) jpn_b13_0610.jpg -> jpn_b13_TS.jpg / WANLF129_RJTD_20260707060000.PNG -> WANLF129_RJTD_TS.PNG
//  クエリ(?_=…)も除去。固定URL(aupa20_00.gif 等)は変化しない。
function imgKey(url) {
  return url.split('?')[0].replace(/_(\d{4,14})(\.\w+)$/i, '_TS$2');
}

// ネット優先（タイムアウト付き）→ 失敗時はキャッシュ。成功時はキャッシュ更新。
async function networkFirstImage(req) {
  const cache = await caches.open(CACHE);
  const key = imgKey(req.url);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), NET_TIMEOUT_MS);
  try {
    const resp = await fetch(req, { signal: ctrl.signal });
    clearTimeout(timer);
    if (resp && (resp.ok || resp.type === 'opaque')) cache.put(key, resp.clone());
    return resp;
  } catch (err) {
    clearTimeout(timer);
    const cached = await cache.match(key);
    if (cached) return cached;
    throw err;
  }
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

  // 画像: ネット優先（常に最新を表示）→ オフライン/失敗時はキャッシュ
  //   ※ 以前は cache-first だったため「全更新」しても古い画像が先に出ていた
  if (req.destination === 'image') {
    e.respondWith(networkFirstImage(req));
    return;
  }

  // その他: ネット優先、失敗時キャッシュ
  e.respondWith(fetch(req).catch(() => caches.match(req)));
});
