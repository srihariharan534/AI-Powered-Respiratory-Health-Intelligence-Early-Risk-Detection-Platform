import React from 'react';
import { NavLink } from 'react-router-dom';
import { useI18n } from '../../context/I18nContext';
import { useFieldApp } from '../../context/FieldAppContext';

export const BottomNav: React.FC = () => {
  const { t } = useI18n();
  const { pendingSyncCount } = useFieldApp();

  const navItems = [
    { path: '/', label: t('nav_home'), icon: '⌂' },
    { path: '/report', label: t('nav_report'), icon: '▲' },
    { path: '/map', label: t('nav_map'), icon: 'map' },
    { path: '/sync', label: t('nav_sync'), icon: '⟳', badge: pendingSyncCount },
  ];

  return (
    <nav
      role="navigation"
      aria-label="Field application primary navigation"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: 'var(--nav-height)',
        backgroundColor: 'var(--bg-surface)',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 100,
        maxWidth: '600px',
        margin: '0 auto',
      }}
    >
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          style={({ isActive }) => ({
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textDecoration: 'none',
            color: isActive ? 'var(--color-brand)' : 'var(--text-muted)',
            fontSize: '0.75rem',
            fontWeight: isActive ? 700 : 500,
            width: '25%',
            height: '100%',
            position: 'relative',
          })}
        >
          <span style={{ fontSize: '1.2rem', marginBottom: '2px' }}>{item.icon}</span>
          <span>{item.label}</span>
          {Boolean(item.badge && item.badge > 0) && (
            <span
              style={{
                position: 'absolute',
                top: '6px',
                right: '25%',
                backgroundColor: 'var(--color-danger)',
                color: '#fff',
                fontSize: '0.65rem',
                fontWeight: 700,
                borderRadius: '10px',
                padding: '0.1rem 0.35rem',
              }}
            >
              {item.badge}
            </span>
          )}
        </NavLink>
      ))}
    </nav>
  );
};
