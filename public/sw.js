// Service Worker for caching R2 images
const CACHE_NAME = 'storiespdf-images-v1';
const R2_DOMAIN = 'pub-141831e61e69445289222976a15b6fb3.r2.dev';

// Cache duration: 1 year in seconds
const CACHE_DURATION = 365 * 24 * 60 * 60 * 1000;

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache requests from R2 domain
  if (url.hostname === R2_DOMAIN) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            // Check if cache is still valid
            const cachedDate = cachedResponse.headers.get('sw-cached-date');
            if (cachedDate) {
              const cacheAge = Date.now() - parseInt(cachedDate, 10);
              if (cacheAge < CACHE_DURATION) {
                return cachedResponse;
              }
            } else {
              // No date header, return cached response anyway
              return cachedResponse;
            }
          }

          // Fetch from network and cache
          return fetch(event.request).then((networkResponse) => {
            if (networkResponse.ok) {
              // Clone the response and add cache date header
              const responseToCache = networkResponse.clone();
              const headers = new Headers(responseToCache.headers);
              headers.set('sw-cached-date', Date.now().toString());

              responseToCache.blob().then((blob) => {
                const cachedResponse = new Response(blob, {
                  status: responseToCache.status,
                  statusText: responseToCache.statusText,
                  headers: headers
                });
                cache.put(event.request, cachedResponse);
              });
            }
            return networkResponse;
          }).catch(() => {
            // Return cached response if network fails
            return cachedResponse;
          });
        });
      })
    );
  }
});
