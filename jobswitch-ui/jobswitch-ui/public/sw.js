// Service Worker for Push Notifications
const CACHE_NAME = 'jobswitch-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install event
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Push event
self.addEventListener('push', (event) => {
  const options = {
    body: 'You have new job recommendations!',
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Jobs',
        icon: '/images/checkmark.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/images/xmark.png'
      }
    ]
  };

  let title = 'JobSwitch.ai';
  let body = 'You have new updates!';

  if (event.data) {
    const data = event.data.json();
    title = data.title || title;
    body = data.body || body;
    
    if (data.type === 'job_alert') {
      body = `${data.count} new job matches found!`;
      options.actions = [
        {
          action: 'view_jobs',
          title: 'View Jobs',
          icon: '/images/job.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/images/close.png'
        }
      ];
    } else if (data.type === 'interview_reminder') {
      body = `Interview reminder: ${data.company} at ${data.time}`;
      options.actions = [
        {
          action: 'prepare',
          title: 'Prepare',
          icon: '/images/interview.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/images/close.png'
        }
      ];
    } else if (data.type === 'skill_recommendation') {
      body = `New skill recommendations available for ${data.role}`;
      options.actions = [
        {
          action: 'view_skills',
          title: 'View Skills',
          icon: '/images/skills.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/images/close.png'
        }
      ];
    }

    options.body = body;
    options.data = data;
  }

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'close') {
    return;
  }

  let url = '/';
  
  if (event.action === 'view_jobs' || event.notification.data?.type === 'job_alert') {
    url = '/?tab=jobs';
  } else if (event.action === 'prepare' || event.notification.data?.type === 'interview_reminder') {
    url = '/?tab=interview';
  } else if (event.action === 'view_skills' || event.notification.data?.type === 'skill_recommendation') {
    url = '/?tab=skills';
  }

  event.waitUntil(
    clients.matchAll().then((clientList) => {
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Background sync for offline functionality
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // Sync any pending data when connection is restored
  try {
    // This would sync any offline actions like job saves, applications, etc.
    console.log('Background sync completed');
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}