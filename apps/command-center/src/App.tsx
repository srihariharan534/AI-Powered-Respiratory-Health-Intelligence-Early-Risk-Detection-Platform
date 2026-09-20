import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { SimulationPage } from './pages/SimulationPage';
import { DigitalTwinPage } from './pages/DigitalTwinPage';
import { HospitalsPage } from './pages/HospitalsPage';
import { SheltersPage } from './pages/SheltersPage';
import { VulnerabilityPage } from './pages/VulnerabilityPage';
import {
  RecommendationsPage,
  AuditPage,
  NotFoundPage,
} from './pages/OperationalPages';
import { JudgeModePage } from './pages/JudgeModePage';


export const App: React.FC = () => {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="incidents" element={<IncidentsPage />} />
            <Route path="simulation" element={<SimulationPage />} />
            <Route path="digital-twin" element={<DigitalTwinPage />} />
            <Route path="hospitals" element={<HospitalsPage />} />
            <Route path="shelters" element={<SheltersPage />} />
            <Route path="vulnerability" element={<VulnerabilityPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="judge-mode" element={<JudgeModePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
};

export default App;
