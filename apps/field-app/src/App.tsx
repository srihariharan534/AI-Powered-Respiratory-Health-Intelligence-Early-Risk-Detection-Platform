import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { I18nProvider } from './context/I18nContext';
import { FieldAppProvider } from './context/FieldAppContext';
import { FieldLayout } from './components/layout/FieldLayout';

// Screens
import { HomeScreen } from './screens/home/HomeScreen';
import { IncidentReportScreen } from './screens/incident-report/IncidentReportScreen';
import { EvidenceCaptureScreen } from './screens/evidence-capture/EvidenceCaptureScreen';
import { AssignmentScreen } from './screens/assignment/AssignmentScreen';
import { CachedMapScreen } from './screens/cached-map/CachedMapScreen';
import { ResourceRequestScreen } from './screens/resource-request/ResourceRequestScreen';
import { SmsFallbackScreen } from './screens/sms-fallback/SmsFallbackScreen';
import { SyncStatusScreen } from './screens/sync-status/SyncStatusScreen';

export const App: React.FC = () => {
  return (
    <I18nProvider>
      <FieldAppProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<FieldLayout />}>
              <Route index element={<HomeScreen />} />
              <Route path="report" element={<IncidentReportScreen />} />
              <Route path="evidence" element={<EvidenceCaptureScreen />} />
              <Route path="assignment" element={<AssignmentScreen />} />
              <Route path="map" element={<CachedMapScreen />} />
              <Route path="resources" element={<ResourceRequestScreen />} />
              <Route path="sms" element={<SmsFallbackScreen />} />
              <Route path="sync" element={<SyncStatusScreen />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </FieldAppProvider>
    </I18nProvider>
  );
};

export default App;
