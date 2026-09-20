import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

export const AppLayout: React.FC = () => {
  return (
    <div className="app-shell">
      <Header />
      <div className="body-container">
        <Sidebar />
        <main className="main-content" role="main">
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  );
};
