# RISE Offline-First Architecture

## Overview

RISE implements a comprehensive offline-first architecture to support farmers in rural areas with poor or intermittent internet connectivity. This ensures critical farming features remain accessible even without an active internet connection.

## Architecture Components

### 1. IndexedDB Storage

**Purpose:** Client-side database for storing offline data

**Stores:**
- `diagnosis_history` - Past crop diagnoses (30-day cache)
- `weather_cache` - Weather information (6-hour cache)
- `market_prices` - Market price data (24-hour cache)
- `forum_posts` - Community forum posts (7-day cache)
- `offline_queue` - Actions pending synchronization

**Configuration:** `infrastructure/offline_config.py`

### 2. Service Worker

**Purpose:** Intercepts network requests and implements caching strategies

**File:** `static/service-worker.js`

**Caching Strategies:**
- **Cache-First:** Static assets (CSS, JS, images)
- **Network-First:** API requests with cache fallback
- **Stale-While-Revalidate:** Dynamic content

**Features:**
- Automatic cache management with size limits
- Background sync for offline actions
- Offline fallback page

### 3. Sync Manager

**Purpose:** Synchronizes offline actions when connection is restored

**File:** `infrastructure/sync_manager.py`

**Sync Priorities:**
1. Diagnosis uploads (highest priority)
2. Forum posts
3. Chat messages
4. Profile updates
5. Analytics (lowest priority)

**Features:**
- Automatic retry with exponential backoff
- Batch synchronization
- Conflict resolution

### 4. Offline Indicator UI

**Purpose:** Visual feedback for online/offline status

**File:** `ui/offline_indicator.py`

**Components:**
- Online/offline status banner
- Sync progress indicator
- Connection status dot
- Storage statistics

## Offline Features

### Available Offline

✅ **View Diagnosis History** - Access past crop diagnoses
✅ **View Cached Weather** - Check recently fetched weather data
✅ **View Market Prices** - See cached market price information
✅ **Read Forum Posts** - Browse cached community discussions (read-only)
✅ **Voice Input** - Record voice queries (synced later)
✅ **Voice Output** - Play cached audio responses
✅ **Chat History** - View previous conversations
✅ **Profile View** - Access user profile and settings

### Requires Connection

❌ **New Diagnoses** - Upload and analyze new crop images
❌ **Live Weather** - Fetch current weather updates
❌ **Live Market Prices** - Get real-time price information
❌ **Forum Posting** - Create new forum posts (queued offline)
❌ **AI Chat** - Get new AI responses (queued offline)

## Usage

### Integration in Streamlit App

```python
from infrastructure.offline_storage import get_storage_manager
from infrastructure.sync_manager import get_sync_manager
from ui.offline_indicator import render_offline_indicator

# Initialize offline support
storage_manager = get_storage_manager()
sync_manager = get_sync_manager()

# Inject offline scripts
st.components.v1.html(storage_manager.generate_indexeddb_init_script(), height=0)
st.components.v1.html(sync_manager.generate_sync_script(), height=0)

# Render offline indicator
render_offline_indicator(language_code="en")
```

### Caching Data

```python
# Cache diagnosis
cached_diagnosis = storage_manager.cache_diagnosis_history({
    "diagnosis_id": "diag_001",
    "user_id": "farmer_123",
    "diagnosis_result": {...}
})

# Cache weather
cached_weather = storage_manager.cache_weather_data("Lucknow", {
    "temperature": 28,
    "humidity": 65
})

# Cache market prices
cached_prices = storage_manager.cache_market_prices("wheat", "Lucknow", {
    "current_price": 2150
})
```

### Creating Offline Actions

```python
# Queue action for later sync
action = storage_manager.create_offline_action("forum_post", {
    "user_id": "farmer_123",
    "title": "Best irrigation practices",
    "content": "..."
})
```

### JavaScript API

```javascript
// Store data offline
await storeOfflineData('diagnosis_history', diagnosisData);

// Retrieve offline data
const diagnosis = await getOfflineData('diagnosis_history', 'diag_001');

// Queue offline action
await queueOfflineAction('forum_post', postData);

// Trigger sync
await syncPendingActions();

// Check online status
const online = isOnline();
```

## Storage Limits

- **IndexedDB:** 50 MB
- **Cache API:** 100 MB
- **Images:** 5 MB per file
- **Audio:** 2 MB per file

## Cache Durations

- **Diagnosis History:** 30 days
- **Weather Data:** 6 hours
- **Market Prices:** 24 hours
- **Forum Posts:** 7 days
- **Static Content:** 30 days

## Sync Behavior

### Automatic Sync Triggers

1. **Connection Restored** - Immediate sync when online
2. **Periodic Check** - Every 5 minutes if online
3. **User Action** - Manual sync via UI button
4. **Background Sync** - Service worker background sync

### Retry Logic

- **Max Retries:** 3 attempts
- **Retry Delay:** 5 seconds
- **Failed Actions:** Marked for manual review

## Testing

Run offline support tests:

```bash
pytest tests/test_offline_support.py -v
```

Run example demonstrations:

```bash
python examples/offline_support_example.py
```

## Browser Compatibility

### Required Features

- **IndexedDB** - All modern browsers
- **Service Workers** - Chrome 40+, Firefox 44+, Safari 11.1+
- **Cache API** - Chrome 40+, Firefox 41+, Safari 11.1+
- **Background Sync** - Chrome 49+, Edge 79+ (optional)

### Fallback Behavior

If service workers are not supported:
- App still functions normally
- No offline caching
- Network requests fail without connection
- Graceful degradation with user notification

## Multilingual Support

Offline indicators support all 9 RISE languages:
- English
- Hindi (हिंदी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Bengali (বাংলা)
- Gujarati (ગુજરાતી)
- Marathi (मराठी)
- Punjabi (ਪੰਜਾਬੀ)

## Performance Optimization

### For 2G/3G Networks

1. **Aggressive Caching** - Cache everything possible
2. **Compression** - Gzip all API responses
3. **Lazy Loading** - Load resources on demand
4. **Image Optimization** - WebP format, progressive loading
5. **Batch Requests** - Combine multiple API calls

### Storage Management

- Automatic cleanup of expired cache
- LRU (Least Recently Used) eviction
- User-configurable cache limits
- Storage usage monitoring

## Security Considerations

### Data Protection

- Encrypted storage for sensitive data
- Secure sync over HTTPS only
- Token-based authentication
- No PII in service worker cache

### Privacy

- User consent for offline storage
- Clear data retention policies
- Easy cache clearing
- Transparent sync status

## Troubleshooting

### Service Worker Not Registering

```javascript
// Check registration status
navigator.serviceWorker.getRegistrations().then(registrations => {
    console.log('Registered service workers:', registrations);
});
```

### IndexedDB Not Working

```javascript
// Check IndexedDB support
if (!window.indexedDB) {
    console.error('IndexedDB not supported');
}
```

### Sync Not Triggering

1. Check online status: `navigator.onLine`
2. Verify pending actions in IndexedDB
3. Check browser console for errors
4. Manually trigger: `window.syncPendingActions()`

## Future Enhancements

- [ ] Progressive Web App (PWA) manifest
- [ ] Push notifications for sync status
- [ ] Conflict resolution UI
- [ ] Offline analytics
- [ ] Peer-to-peer sync via WebRTC
- [ ] Selective sync preferences
- [ ] Bandwidth usage monitoring

## References

- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [Cache API](https://developer.mozilla.org/en-US/docs/Web/API/Cache)
- [Background Sync API](https://developer.mozilla.org/en-US/docs/Web/API/Background_Synchronization_API)

## Support

For issues or questions about offline functionality:
1. Check browser console for errors
2. Review storage stats in sidebar
3. Test with example scripts
4. Check sync status in UI

---

**Built for rural India** 🌾 **Designed for intermittent connectivity** 📡 **Optimized for 2G/3G networks** 📱
