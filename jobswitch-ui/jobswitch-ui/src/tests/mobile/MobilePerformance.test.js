import { debounce, throttle, VirtualScroller, memoryUtils, networkUtils } from '../../utils/mobileOptimizations';

describe('Mobile Performance Utilities', () => {
  describe('debounce', () => {
    jest.useFakeTimers();

    it('should debounce function calls', () => {
      const mockFn = jest.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      expect(mockFn).not.toHaveBeenCalled();

      jest.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    afterEach(() => {
      jest.clearAllTimers();
    });
  });

  describe('throttle', () => {
    jest.useFakeTimers();

    it('should throttle function calls', () => {
      const mockFn = jest.fn();
      const throttledFn = throttle(mockFn, 100);

      throttledFn();
      throttledFn();
      throttledFn();

      expect(mockFn).toHaveBeenCalledTimes(1);

      jest.advanceTimersByTime(100);
      throttledFn();

      expect(mockFn).toHaveBeenCalledTimes(2);
    });

    afterEach(() => {
      jest.clearAllTimers();
    });
  });

  describe('VirtualScroller', () => {
    it('should calculate visible range correctly', () => {
      const scroller = new VirtualScroller(400, 50, 2);
      const range = scroller.getVisibleRange(100, 100);

      expect(range.start).toBe(0); // Math.max(0, 2 - 2)
      expect(range.end).toBe(12); // Math.min(99, 10 + 2)
      expect(range.offsetY).toBe(0);
    });

    it('should handle edge cases', () => {
      const scroller = new VirtualScroller(400, 50, 2);
      const range = scroller.getVisibleRange(0, 5);

      expect(range.start).toBe(0);
      expect(range.end).toBe(4); // totalItems - 1
    });
  });

  describe('memoryUtils', () => {
    it('should provide memory info when available', () => {
      // Mock performance.memory
      Object.defineProperty(performance, 'memory', {
        value: {
          usedJSHeapSize: 1000000,
          totalJSHeapSize: 2000000,
          jsHeapSizeLimit: 4000000
        },
        configurable: true
      });

      const memoryInfo = memoryUtils.getMemoryInfo();
      
      expect(memoryInfo).toEqual({
        used: 1000000,
        total: 2000000,
        limit: 4000000
      });
    });

    it('should return null when memory info is not available', () => {
      // Remove performance.memory
      delete performance.memory;

      const memoryInfo = memoryUtils.getMemoryInfo();
      expect(memoryInfo).toBeNull();
    });
  });

  describe('networkUtils', () => {
    it('should detect connection type when available', () => {
      // Mock navigator.connection
      Object.defineProperty(navigator, 'connection', {
        value: {
          effectiveType: '4g'
        },
        configurable: true
      });

      const connectionType = networkUtils.getConnectionType();
      expect(connectionType).toBe('4g');
    });

    it('should return unknown when connection info is not available', () => {
      // Remove navigator.connection
      delete navigator.connection;

      const connectionType = networkUtils.getConnectionType();
      expect(connectionType).toBe('unknown');
    });

    it('should detect slow connections', () => {
      Object.defineProperty(navigator, 'connection', {
        value: {
          effectiveType: '2g',
          saveData: false
        },
        configurable: true
      });

      const isSlowConnection = networkUtils.isSlowConnection();
      expect(isSlowConnection).toBe(true);
    });

    it('should detect save data mode', () => {
      Object.defineProperty(navigator, 'connection', {
        value: {
          effectiveType: '4g',
          saveData: true
        },
        configurable: true
      });

      const isSlowConnection = networkUtils.isSlowConnection();
      expect(isSlowConnection).toBe(true);
    });

    it('should preload resources', () => {
      // Mock document.head.appendChild
      const mockAppendChild = jest.fn();
      Object.defineProperty(document, 'head', {
        value: {
          appendChild: mockAppendChild
        },
        configurable: true
      });

      networkUtils.preloadResource('/api/jobs', 'fetch');

      expect(mockAppendChild).toHaveBeenCalledTimes(1);
      const linkElement = mockAppendChild.mock.calls[0][0];
      expect(linkElement.rel).toBe('preload');
      expect(linkElement.href).toBe('/api/jobs');
      expect(linkElement.as).toBe('fetch');
    });
  });
});

describe('Mobile Component Performance', () => {
  it('should handle large lists efficiently', () => {
    const startTime = performance.now();
    
    // Simulate rendering a large list
    const items = Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      title: `Item ${i}`,
      description: `Description for item ${i}`
    }));

    // Simulate virtual scrolling
    const scroller = new VirtualScroller(400, 50);
    const visibleRange = scroller.getVisibleRange(0, items.length);
    const visibleItems = items.slice(visibleRange.start, visibleRange.end + 1);

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render quickly (less than 10ms for this simple operation)
    expect(renderTime).toBeLessThan(10);
    expect(visibleItems.length).toBeLessThan(items.length);
    expect(visibleItems.length).toBeGreaterThan(0);
  });

  it('should optimize image loading', async () => {
    // Mock Image constructor
    global.Image = class {
      constructor() {
        // Immediately call onload for test
        setTimeout(() => {
          if (this.onload) {
            this.onload();
          }
        }, 1);
      }
    };

    const { lazyLoadImage } = require('../../utils/mobileOptimizations');
    
    const result = await lazyLoadImage('/test-image.jpg');
    expect(result).toBe('/test-image.jpg');
  }, 1000);
});

describe('Touch Gesture Performance', () => {
  it('should handle touch events efficiently', () => {
    const { TouchGestureDetector } = require('../../utils/mobileOptimizations');
    
    // Create a mock element
    const mockElement = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };

    const detector = new TouchGestureDetector(mockElement);

    // Should bind events
    expect(mockElement.addEventListener).toHaveBeenCalledWith('touchstart', expect.any(Function), { passive: true });
    expect(mockElement.addEventListener).toHaveBeenCalledWith('touchend', expect.any(Function), { passive: true });

    // Should clean up properly
    detector.destroy();
    expect(mockElement.removeEventListener).toHaveBeenCalledTimes(2);
  });

  it('should detect swipe gestures correctly', () => {
    const { TouchGestureDetector } = require('../../utils/mobileOptimizations');
    
    const mockElement = {
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };

    const detector = new TouchGestureDetector(mockElement, { threshold: 50 });
    const mockOnSwipe = jest.fn();
    detector.onSwipe = mockOnSwipe;

    // Simulate touch events
    const touchStartEvent = {
      touches: [{ clientX: 100, clientY: 100 }]
    };

    const touchEndEvent = {
      changedTouches: [{ clientX: 200, clientY: 100 }]
    };

    // Get the bound handlers
    const touchStartHandler = mockElement.addEventListener.mock.calls[0][1];
    const touchEndHandler = mockElement.addEventListener.mock.calls[1][1];

    // Simulate swipe right
    touchStartHandler(touchStartEvent);
    touchEndHandler(touchEndEvent);

    expect(mockOnSwipe).toHaveBeenCalledWith('right', expect.any(Object));
  });
});

describe('Accessibility Performance', () => {
  it('should announce to screen readers efficiently', () => {
    const { a11yUtils } = require('../../utils/mobileOptimizations');
    
    // Mock document.body
    const mockAppendChild = jest.fn();
    const mockRemoveChild = jest.fn();
    Object.defineProperty(document, 'body', {
      value: {
        appendChild: mockAppendChild,
        removeChild: mockRemoveChild
      },
      configurable: true
    });

    jest.useFakeTimers();

    a11yUtils.announce('Test message', 'polite');

    expect(mockAppendChild).toHaveBeenCalledWith(
      expect.objectContaining({
        textContent: 'Test message'
      })
    );

    jest.advanceTimersByTime(1000);

    expect(mockRemoveChild).toHaveBeenCalled();

    jest.useRealTimers();
  });

  it('should trap focus efficiently', () => {
    const { a11yUtils } = require('../../utils/mobileOptimizations');
    
    // Create mock focusable elements
    const mockButton1 = { focus: jest.fn() };
    const mockButton2 = { focus: jest.fn() };
    
    const mockElement = {
      querySelectorAll: jest.fn().mockReturnValue([mockButton1, mockButton2]),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    };

    const cleanup = a11yUtils.trapFocus(mockElement);

    expect(mockElement.addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
    expect(mockButton1.focus).toHaveBeenCalled();

    // Should provide cleanup function
    expect(typeof cleanup).toBe('function');
    
    cleanup();
    expect(mockElement.removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
  });
});