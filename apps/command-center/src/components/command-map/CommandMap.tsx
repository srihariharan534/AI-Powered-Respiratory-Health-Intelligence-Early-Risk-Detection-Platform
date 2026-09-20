/**
 * Interactive Command Map for NEXUS Command Center
 * Built with Leaflet using native WGS84 [lat, lon] mapping from GeoJSON [lon, lat].
 * Cleanly isolates map lifecycle, GeoJSON validation, and vector rendering.
 */

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  FloodExtentFeature,
  RoadFeature,
  BridgeFeature,
  IncidentSummary,
  FacilitySummary,
  RouteFeature,
  GisSelectedEntity,
} from '../../types';

interface CommandMapProps {
  center: [number, number]; // [lon, lat]
  zoom: number;
  floodFeatures: FloodExtentFeature[];
  roadFeatures: RoadFeature[];
  bridgeFeatures: BridgeFeature[];
  incidents: IncidentSummary[];
  hospitals: FacilitySummary[];
  shelters: FacilitySummary[];
  routes: RouteFeature[];
  visibleLayers: {
    flood: boolean;
    roads: boolean;
    bridges: boolean;
    incidents: boolean;
    facilities: boolean;
    routes: boolean;
  };
  selectedEntity: GisSelectedEntity;
  onSelectEntity: (entity: GisSelectedEntity) => void;
}

export const CommandMap: React.FC<CommandMapProps> = ({
  center,
  zoom,
  floodFeatures,
  roadFeatures,
  bridgeFeatures,
  incidents,
  hospitals,
  shelters,
  routes,
  visibleLayers,
  selectedEntity,
  onSelectEntity,
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersGroupRef = useRef<L.LayerGroup | null>(null);

  // 1. Initialize Map Instance
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Notice Leaflet expects [latitude, longitude]
    const map = L.map(mapContainerRef.current, {
      center: [center[1], center[0]],
      zoom,
      zoomControl: true,
      attributionControl: false,
    });

    // Dark-themed tile layer (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    const layersGroup = L.layerGroup().addTo(map);
    layersGroupRef.current = layersGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Synchronize Center/Zoom
  useEffect(() => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView([center[1], center[0]], zoom);
    }
  }, [center, zoom]);

  // 3. Render Vector and Marker Layers based on visibleLayers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = layersGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();

    // A. Flood Extent Polygons (Phase 10 Output)
    if (visibleLayers.flood) {
      floodFeatures.forEach((feat) => {
        try {
          // Convert GeoJSON [lon, lat] rings to Leaflet [lat, lon]
          const latLngs = feat.geometry.coordinates[0].map(([lon, lat]) => [lat, lon] as [number, number]);
          const isSelected = selectedEntity?.type === 'FLOOD' && selectedEntity.data.id === feat.id;

          const polygon = L.polygon(latLngs, {
            color: feat.properties.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b',
            weight: isSelected ? 3 : 1.5,
            fillColor: feat.properties.severity === 'CRITICAL' ? '#ef4444' : '#f59e0b',
            fillOpacity: isSelected ? 0.45 : 0.25,
            dashArray: feat.properties.mode === 'SIMULATION' ? '4, 4' : undefined,
          });

          polygon.on('click', () => {
            onSelectEntity({ type: 'FLOOD', data: { ...feat.properties, id: feat.id } });
          });

          polygon.bindTooltip(
            `<strong>Flood Hazard: ${feat.properties.name}</strong><br/>Severity: ${feat.properties.severity} • ${feat.properties.mode}`,
            { sticky: true }
          );

          polygon.addTo(group);
        } catch (e) {
          console.warn('Invalid flood geometry:', feat.id, e);
        }
      });
    }

    // B. Roads (Phase 05 OSM + Phase 08 Dynamic Overlay)
    if (visibleLayers.roads) {
      roadFeatures.forEach((road) => {
        try {
          const latLngs = road.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);
          const isSelected = selectedEntity?.type === 'ROAD' && selectedEntity.data.id === road.id;
          const isBlocked = road.properties.status === 'BLOCKED';

          const polyline = L.polyline(latLngs, {
            color: isBlocked ? '#ef4444' : '#10b981',
            weight: isSelected ? 6 : 3.5,
            opacity: isBlocked ? 0.9 : 0.6,
            dashArray: isBlocked ? '6, 6' : undefined,
          });

          polyline.on('click', () => {
            onSelectEntity({ type: 'ROAD', data: { ...road.properties, id: road.id } });
          });

          polyline.bindTooltip(
            `<strong>${road.properties.name}</strong><br/>Status: ${road.properties.status}`,
            { sticky: true }
          );

          polyline.addTo(group);
        } catch (e) {
          console.warn('Invalid road geometry:', road.id, e);
        }
      });
    }

    // C. Dynamic Routes (Phase 07 Dijkstra / Phase 08 Dynamic Rerouting)
    if (visibleLayers.routes) {
      routes.forEach((route) => {
        try {
          const latLngs = route.geometry.coordinates.map(([lon, lat]) => [lat, lon] as [number, number]);
          const isSelected = selectedEntity?.type === 'ROUTE' && selectedEntity.data.id === route.id;

          const polyline = L.polyline(latLngs, {
            color: route.properties.status === 'BLOCKED' ? '#dc2626' : '#3b82f6',
            weight: isSelected ? 7 : 4.5,
            dashArray: route.properties.status === 'BLOCKED' ? '8, 6' : undefined,
            opacity: route.properties.isCurrent ? 1.0 : 0.5,
          });

          polyline.on('click', () => {
            onSelectEntity({ type: 'ROUTE', data: { ...route.properties, id: route.id } });
          });

          polyline.bindTooltip(
            `<strong>${route.properties.name}</strong><br/>${route.properties.distanceKm} km • ${route.properties.travelTimeMin} min`,
            { sticky: true }
          );

          polyline.addTo(group);
        } catch (e) {
          console.warn('Invalid route geometry:', route.id, e);
        }
      });
    }

    // D. Bridges (Phase 08/09)
    if (visibleLayers.bridges) {
      bridgeFeatures.forEach((bridge) => {
        const [lon, lat] = bridge.geometry.coordinates;
        const isSelected = selectedEntity?.type === 'BRIDGE' && selectedEntity.data.id === bridge.id;

        const circle = L.circleMarker([lat, lon], {
          radius: isSelected ? 8 : 6,
          fillColor: bridge.properties.status === 'FAILED' ? '#ef4444' : '#64748b',
          color: '#ffffff',
          weight: 1.5,
          fillOpacity: 0.9,
        });

        circle.on('click', () => {
          onSelectEntity({ type: 'BRIDGE', data: { ...bridge.properties, id: bridge.id } });
        });

        circle.bindTooltip(`<strong>Bridge: ${bridge.properties.name}</strong><br/>Status: ${bridge.properties.status}`);
        circle.addTo(group);
      });
    }

    // E. Incidents (Phase 04 Data Contracts)
    if (visibleLayers.incidents) {
      incidents.forEach((inc) => {
        const isSelected = selectedEntity?.type === 'INCIDENT' && selectedEntity.data.id === inc.id;
        const color = inc.severity === 'CRITICAL' ? '#ef4444' : inc.severity === 'HIGH' ? '#f97316' : '#f59e0b';

        const marker = L.circleMarker([inc.latitude, inc.longitude], {
          radius: isSelected ? 9 : 6.5,
          fillColor: color,
          color: '#ffffff',
          weight: 2,
          fillOpacity: 1.0,
        });

        marker.on('click', () => {
          onSelectEntity({ type: 'INCIDENT', data: inc });
        });

        marker.bindTooltip(`<strong>Incident: ${inc.id}</strong><br/>${inc.type} • ${inc.severity}`);
        marker.addTo(group);
      });
    }

    // F. Facilities (Hospitals & Shelters)
    if (visibleLayers.facilities) {
      hospitals.forEach((hosp) => {
        if (!hosp.latitude || !hosp.longitude) return;
        const isSelected = selectedEntity?.type === 'HOSPITAL' && selectedEntity.data.id === hosp.id;
        const isExposed = hosp.floodExposure?.is_exposed;
        const hospStatus = hosp.operationalStatus || 'OPERATIONAL';

        // Color semantics based on status
        let fillColor = '#10b981'; // OPERATIONAL (Green)
        if (hospStatus === 'OVERLOADED') fillColor = '#f59e0b'; // Amber
        else if (hospStatus === 'EVACUATING' || hospStatus === 'CLOSED') fillColor = '#ef4444'; // Red

        const marker = L.circleMarker([hosp.latitude, hosp.longitude], {
          radius: isSelected ? 10 : 7.5,
          fillColor: fillColor,
          color: isExposed ? '#3b82f6' : '#ffffff',
          weight: isExposed ? 3 : 2,
          fillOpacity: 0.95,
        });

        marker.on('click', () => {
          onSelectEntity({ type: 'HOSPITAL', data: hosp });
        });

        const available = hosp.capacityTotal - hosp.capacityOccupied;
        const exposedTag = isExposed ? '<br/><span style="color:#60a5fa;font-weight:bold;">⚠️ IN FLOOD ZONE (EXPOSED)</span>' : '';
        marker.bindTooltip(
          `<strong>✚ [HOSPITAL] ${hosp.name}</strong><br/>Status: ${hospStatus}<br/>Available: ${available}/${hosp.capacityTotal} beds • ICU: ${hosp.icuAvailable ?? 0}${exposedTag}`,
          { sticky: true }
        );
        marker.addTo(group);
      });

      shelters.forEach((shelt) => {
        if (!shelt.latitude || !shelt.longitude) return;
        const isSelected = selectedEntity?.type === 'SHELTER' && selectedEntity.data.id === shelt.id;
        const isExposed = shelt.floodExposure?.is_exposed;
        const sheltStatus = shelt.operationalStatus || 'OPEN';

        let fillColor = '#06b6d4'; // OPEN (Cyan/teal)
        if (sheltStatus === 'AT_CAPACITY') fillColor = '#f59e0b'; // Amber
        else if (sheltStatus === 'STANDBY') fillColor = '#8b5cf6'; // Purple
        else if (sheltStatus === 'CLOSED') fillColor = '#ef4444'; // Red

        const marker = L.circleMarker([shelt.latitude, shelt.longitude], {
          radius: isSelected ? 10 : 7.5,
          fillColor: fillColor,
          color: isExposed ? '#3b82f6' : '#ffffff',
          weight: isExposed ? 3 : 2,
          fillOpacity: 0.95,
        });

        marker.on('click', () => {
          onSelectEntity({ type: 'SHELTER', data: shelt });
        });

        const available = shelt.capacityTotal - shelt.capacityOccupied;
        const exposedTag = isExposed ? '<br/><span style="color:#60a5fa;font-weight:bold;">⚠️ IN FLOOD ZONE (EXPOSED)</span>' : '';
        marker.bindTooltip(
          `<strong>⛺ [SHELTER] ${shelt.name}</strong><br/>Status: ${sheltStatus}<br/>Available: ${available}/${shelt.capacityTotal} spots${exposedTag}`,
          { sticky: true }
        );
        marker.addTo(group);
      });
    }

  }, [
    floodFeatures,
    roadFeatures,
    bridgeFeatures,
    incidents,
    hospitals,
    shelters,
    routes,
    visibleLayers,
    selectedEntity,
  ]);

  return (
    <div
      ref={mapContainerRef}
      role="application"
      aria-label="NEXUS Emergency Command Map"
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: '#0a0d14',
        borderRadius: '6px',
        overflow: 'hidden',
      }}
    />
  );
};
