import React from 'react';
import { Outlet } from 'react-router-dom';
import { FieldHeader } from './FieldHeader';
import { BottomNav } from './BottomNav';

export const FieldLayout: React.FC = () => {
  return (
    <div className="field-container">
      <FieldHeader />
      <main className="screen-content" role="main">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
};
