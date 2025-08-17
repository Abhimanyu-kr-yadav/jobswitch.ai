class PushNotificationService {
  constructor() {
    this.registration = null;
    this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    this.permission = Notification.permission;
  }

  async initialize() {
    if (!this.isSupported) {
      console.warn('Push notifications are not supported in this browser');
      return false;
    }

    try {
      // Register service worker
      this.registration = await navigator.serviceWorker.register('/sw.js');
      console.log('Service Worker registered successfully');
      return true;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return false;
    }
  }

  async requestPermission() {
    if (!this.isSupported) {
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    if (this.permission === 'denied') {
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  async subscribe(userId) {
    if (!this.registration || this.permission !== 'granted') {
      return null;
    }

    try {
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(
          process.env.REACT_APP_VAPID_PUBLIC_KEY || 'your-vapid-public-key'
        )
      });

      // Send subscription to backend
      await this.sendSubscriptionToBackend(subscription, userId);
      return subscription;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      return null;
    }
  }

  async sendSubscriptionToBackend(subscription, userId) {
    try {
      const response = await fetch('/api/v1/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subscription,
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to send subscription to backend');
      }
    } catch (error) {
      console.error('Error sending subscription to backend:', error);
    }
  }

  async unsubscribe() {
    if (!this.registration) {
      return false;
    }

    try {
      const subscription = await this.registration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
        // Notify backend about unsubscription
        await this.sendUnsubscriptionToBackend(subscription);
      }
      return true;
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      return false;
    }
  }

  async sendUnsubscriptionToBackend(subscription) {
    try {
      await fetch('/api/v1/notifications/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ subscription })
      });
    } catch (error) {
      console.error('Error sending unsubscription to backend:', error);
    }
  }

  // Show local notification (fallback for when push isn't available)
  showLocalNotification(title, options = {}) {
    if (this.permission !== 'granted') {
      return false;
    }

    try {
      new Notification(title, {
        icon: '/logo192.png',
        badge: '/logo192.png',
        ...options
      });
      return true;
    } catch (error) {
      console.error('Error showing local notification:', error);
      return false;
    }
  }

  // Utility function to convert VAPID key
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Check if notifications are supported and enabled
  isEnabled() {
    return this.isSupported && this.permission === 'granted';
  }

  // Get current subscription status
  async getSubscriptionStatus() {
    if (!this.registration) {
      return null;
    }

    try {
      const subscription = await this.registration.pushManager.getSubscription();
      return subscription;
    } catch (error) {
      console.error('Error getting subscription status:', error);
      return null;
    }
  }
}

export default new PushNotificationService();