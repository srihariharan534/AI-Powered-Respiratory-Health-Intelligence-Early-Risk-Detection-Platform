import React from 'react';
import { NavLink } from 'react-router-dom';

interface NavSection {
  title: string;
  items: { label: string; path: string; icon: string }[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'COMMAND',
    items: [{ label: 'Dashboard', path: '/dashboard', icon: '▦' }],
  },
  {
    title: 'OPERATIONS',
    items: [
      { label: 'Incidents', path: '/incidents', icon: '▲' }],
  },
  {
    title: 'FACILITIES',
    items: [
      { label: 'Hospitals', path: '/hospitals', icon: '✚' },
      { label: 'Shelters', path: '/shelters', icon: '⛺' },
      { label: 'Vulnerability', path: '/vulnerability', icon: '◎' },
    ],
  },
  {
    title: 'SIMULATION',
    items: [
      { label: 'What-If Simulation', path: '/simulation', icon: '⚙' },
      { label: 'Digital Twin', path: '/digital-twin', icon: '⧉' },
    ],
  },
  {
    title: 'DECISION',
    items: [{ label: 'Recommendations', path: '/recommendations', icon: '✦' }],
  },
  {
    title: 'GOVERNANCE',
    items: [{ label: 'Audit & Provenance', path: '/audit', icon: '▤' }],
  },
  {
    title: 'DEMO',
    items: [{ label: 'Judge Mode', path: '/judge-mode', icon: '⚖' }],
  },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar" role="navigation" aria-label="Command Center Navigation">
      {NAV_SECTIONS.map((section) => (
        <div key={section.title}>
          <div className="nav-section-title">{section.title}</div>
          <ul className="nav-list">
            {section.items.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-item-link ${isActive ? 'active' : ''}`
                  }
                  end={item.path === '/dashboard'}
                >
                  <span style={{ fontSize: '1rem', width: '18px', textAlign: 'center' }}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </aside>
  );
};
