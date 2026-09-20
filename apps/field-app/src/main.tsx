import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/field-app.css';
import { ServiceWorkerCoordinator } from './service-worker/offline-sync';

// Register Service Worker in browser environment without blocking UI mount
if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    ServiceWorkerCoordinator.getInstance()
      .register()
      .catch((err) => {
        console.warn('Service Worker registration skipped or failed:', err);
      });
  });
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
