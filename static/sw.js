const CACHE_NAME = 'video-downloader-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/style.css',
    '/static/script.js',
    '/static/manifest.json'
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
});

// Fetch event - network falling back to cache
self.addEventListener('fetch', (event) => {
    // Only intercept GET requests, skip API calls (we don't want to cache video downloads!)
    if (event.request.method !== 'GET' || event.request.url.includes('/api/')) {
        return;
    }

    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});
