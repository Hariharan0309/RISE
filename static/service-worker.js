/**
 * RISE Service Worker
 * Implements offline-first caching strategies for rural connectivity
 */

const CACHE_VERSION = 'rise-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Resources to cache immediately
const STATIC_ASSETS = [
    '/',
    '/app.py',
    '/static/offline.html'
];

// Cache size limits
const CACHE_LIMITS = {
    [DYNAMIC_CACHE]: 50,
    [IMAGE_CACHE]: 100,
    [API_CACHE]: 30
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('rise-') && name !== CACHE_VERSION)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Choose strategy based on request type
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
    } else if (isImage(url)) {
        event.respondWith(cacheFirst(request, IMAGE_CACHE));
    } else if (isAPIRequest(url)) {
        event.respondWith(networkFirst(request, API_CACHE));
    } else {
        event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
    }
});

// Cache-first strategy (for static assets)
async function cacheFirst(request, cacheName) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
            await limitCacheSize(cacheName);
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[Service Worker] Fetch failed:', error);
        return getOfflineFallback(request);
    }
}

// Network-first strategy (for API requests)
async function networkFirst(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
            await limitCacheSize(cacheName);
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Network failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return getOfflineFallback(request);
    }
}

// Stale-while-revalidate strategy (for dynamic content)
async function staleWhileRevalidate(request, cacheName) {
    const cachedResponse = await caches.match(request);
    
    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                const cache = caches.open(cacheName);
                cache.then((c) => {
                    c.put(request, networkResponse.clone());
                    limitCacheSize(cacheName);
                });
            }
            return networkResponse;
        })
        .catch((error) => {
            console.error('[Service Worker] Fetch failed:', error);
            return cachedResponse || getOfflineFallback(request);
        });
    
    return cachedResponse || fetchPromise;
}

// Limit cache size
async function limitCacheSize(cacheName) {
    const limit = CACHE_LIMITS[cacheName];
    
    if (!limit) return;
    
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > limit) {
        // Remove oldest entries
        const toDelete = keys.slice(0, keys.length - limit);
        await Promise.all(toDelete.map((key) => cache.delete(key)));
    }
}

// Get offline fallback
function getOfflineFallback(request) {
    const url = new URL(request.url);
    
    if (request.destination === 'document') {
        return caches.match('/static/offline.html');
    }
    
    if (isImage(url)) {
        return new Response(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect fill="#ddd" width="200" height="200"/><text x="50%" y="50%" text-anchor="middle" fill="#999">Offline</text></svg>',
            { headers: { 'Content-Type': 'image/svg+xml' } }
        );
    }
    
    return new Response('Offline', {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'text/plain' }
    });
}

// Helper functions
function isStaticAsset(url) {
    return url.pathname.match(/\.(css|js|woff2?|ttf|eot)$/);
}

function isImage(url) {
    return url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/);
}

function isAPIRequest(url) {
    return url.pathname.startsWith('/api/');
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);
    
    if (event.tag === 'sync-offline-actions') {
        event.waitUntil(syncOfflineActions());
    }
});

async function syncOfflineActions() {
    try {
        // Open IndexedDB and get pending actions
        const db = await openIndexedDB();
        const actions = await getPendingActions(db);
        
        for (const action of actions) {
            try {
                await syncAction(action);
                await markActionSynced(db, action.action_id);
            } catch (error) {
                console.error('[Service Worker] Failed to sync action:', error);
                await incrementRetryCount(db, action.action_id);
            }
        }
    } catch (error) {
        console.error('[Service Worker] Sync failed:', error);
    }
}

function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('rise_offline_db', 1);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function getPendingActions(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offline_queue'], 'readonly');
        const store = transaction.objectStore('offline_queue');
        const request = store.getAll();
        
        request.onsuccess = () => {
            const actions = request.result.filter(a => a.sync_status === 'pending');
            resolve(actions);
        };
        request.onerror = () => reject(request.error);
    });
}

async function syncAction(action) {
    const endpoint = getActionEndpoint(action.action_type);
    
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action.action_data)
    });
    
    if (!response.ok) {
        throw new Error(`Sync failed: ${response.status}`);
    }
    
    return response.json();
}

function getActionEndpoint(actionType) {
    const endpoints = {
        'diagnosis_upload': '/api/v1/diagnosis/crop-disease',
        'forum_post': '/api/v1/community/discussions',
        'chat_message': '/api/v1/chat/message',
        'profile_update': '/api/v1/user/profile'
    };
    return endpoints[actionType] || '/api/v1/sync';
}

function markActionSynced(db, actionId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offline_queue'], 'readwrite');
        const store = transaction.objectStore('offline_queue');
        const request = store.get(actionId);
        
        request.onsuccess = () => {
            const action = request.result;
            action.sync_status = 'synced';
            action.synced_at = Date.now();
            
            const updateRequest = store.put(action);
            updateRequest.onsuccess = () => resolve();
            updateRequest.onerror = () => reject(updateRequest.error);
        };
        request.onerror = () => reject(request.error);
    });
}

function incrementRetryCount(db, actionId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offline_queue'], 'readwrite');
        const store = transaction.objectStore('offline_queue');
        const request = store.get(actionId);
        
        request.onsuccess = () => {
            const action = request.result;
            action.retry_count = (action.retry_count || 0) + 1;
            
            if (action.retry_count >= 3) {
                action.sync_status = 'failed';
            }
            
            const updateRequest = store.put(action);
            updateRequest.onsuccess = () => resolve();
            updateRequest.onerror = () => reject(updateRequest.error);
        };
        request.onerror = () => reject(request.error);
    });
}

// Push notifications for sync status
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    
    const options = {
        body: data.body || 'RISE notification',
        icon: '/static/icon-192.png',
        badge: '/static/badge-72.png',
        data: data
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'RISE', options)
    );
});

console.log('[Service Worker] Loaded successfully');
