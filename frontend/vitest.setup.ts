import '@testing-library/jest-dom';

// Polyfill ResizeObserver for React Flow and other canvas components in JSDOM
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock;
if (typeof window !== 'undefined') {
  window.ResizeObserver = ResizeObserverMock;
}
