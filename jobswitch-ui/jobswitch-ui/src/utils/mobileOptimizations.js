// Mobile performance optimization utilities

/**
 * Lazy loading utility for images
 */
export const lazyLoadImage = (src, placeholder = '/placeholder.png') => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(src);
    img.onerror = () => resolve(placeholder);
    img.src = src;
  });
};

/**
 * Debounce function for search inputs
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle function for scroll events
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Virtual scrolling utility for large lists
 */
export class VirtualScroller {
  constructor(containerHeight, itemHeight, buffer = 5) {
    this.containerHeight = containerHeight;
    this.itemHeight = itemHeight;
    this.buffer = buffer;
  }

  getVisibleRange(scrollTop, totalItems) {
    const visibleStart = Math.floor(scrollTop / this.itemHeight);
    const visibleEnd = Math.min(
      visibleStart + Math.ceil(this.containerHeight / this.itemHeight),
      totalItems - 1
    );

    return {
      start: Math.max(0, visibleStart - this.buffer),
      end: Math.min(totalItems - 1, visibleEnd + this.buffer),
      offsetY: Math.max(0, visibleStart - this.buffer) * this.itemHeight
    };
  }
}

/**
 * Touch gesture detection
 */
export class TouchGestureDetector {
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      threshold: 50,
      timeout: 300,
      ...options
    };
    
    this.startX = 0;
    this.startY = 0;
    this.startTime = 0;
    
    this.bindEvents();
  }

  bindEvents() {
    this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    this.element.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
  }

  handleTouchStart(e) {
    const touch = e.touches[0];
    this.startX = touch.clientX;
    this.startY = touch.clientY;
    this.startTime = Date.now();
  }

  handleTouchEnd(e) {
    const touch = e.changedTouches[0];
    const endX = touch.clientX;
    const endY = touch.clientY;
    const endTime = Date.now();

    const deltaX = endX - this.startX;
    const deltaY = endY - this.startY;
    const deltaTime = endTime - this.startTime;

    if (deltaTime > this.options.timeout) return;

    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    if (absX > this.options.threshold && absX > absY) {
      // Horizontal swipe
      const direction = deltaX > 0 ? 'right' : 'left';
      this.onSwipe?.(direction, { deltaX, deltaY, deltaTime });
    } else if (absY > this.options.threshold && absY > absX) {
      // Vertical swipe
      const direction = deltaY > 0 ? 'down' : 'up';
      this.onSwipe?.(direction, { deltaX, deltaY, deltaTime });
    }
  }

  onSwipe(direction, details) {
    // Override this method
  }

  destroy() {
    this.element.removeEventListener('touchstart', this.handleTouchStart);
    this.element.removeEventListener('touchend', this.handleTouchEnd);
  }
}

/**
 * Intersection Observer utility for lazy loading
 */
export const createIntersectionObserver = (callback, options = {}) => {
  const defaultOptions = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options
  };

  return new IntersectionObserver(callback, defaultOptions);
};

/**
 * Memory management utilities
 */
export const memoryUtils = {
  // Clear unused images from memory
  clearImageCache: () => {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
      if (!img.getBoundingClientRect().top < window.innerHeight + 200) {
        img.src = '';
      }
    });
  },

  // Monitor memory usage (if available)
  getMemoryInfo: () => {
    if ('memory' in performance) {
      return {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit
      };
    }
    return null;
  },

  // Force garbage collection (development only)
  forceGC: () => {
    if (window.gc && typeof window.gc === 'function') {
      window.gc();
    }
  }
};

/**
 * Network optimization utilities
 */
export const networkUtils = {
  // Check connection type
  getConnectionType: () => {
    if ('connection' in navigator) {
      return navigator.connection.effectiveType;
    }
    return 'unknown';
  },

  // Check if on slow connection
  isSlowConnection: () => {
    if ('connection' in navigator) {
      const connection = navigator.connection;
      return connection.effectiveType === 'slow-2g' || 
             connection.effectiveType === '2g' ||
             connection.saveData;
    }
    return false;
  },

  // Preload critical resources
  preloadResource: (url, type = 'fetch') => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = url;
    link.as = type;
    document.head.appendChild(link);
  }
};

/**
 * Battery optimization utilities
 */
export const batteryUtils = {
  // Check battery status
  getBatteryInfo: async () => {
    if ('getBattery' in navigator) {
      try {
        const battery = await navigator.getBattery();
        return {
          level: battery.level,
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      } catch (error) {
        console.warn('Battery API not available:', error);
      }
    }
    return null;
  },

  // Check if device is in power saving mode
  isPowerSavingMode: async () => {
    const batteryInfo = await batteryUtils.getBatteryInfo();
    return batteryInfo && batteryInfo.level < 0.2 && !batteryInfo.charging;
  }
};

/**
 * Accessibility utilities for mobile
 */
export const a11yUtils = {
  // Announce to screen readers
  announce: (message, priority = 'polite') => {
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    announcer.textContent = message;
    
    document.body.appendChild(announcer);
    setTimeout(() => document.body.removeChild(announcer), 1000);
  },

  // Focus management
  trapFocus: (element) => {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    element.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => element.removeEventListener('keydown', handleTabKey);
  }
};