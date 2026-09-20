# Field Officer Operational Workflow (Phase 22 UX)

This document outlines the standard operating procedures and user experience flows for field personnel using the NEXUS Field PWA.

---

## 1. Initial Briefing & Assignment Tracking
1. Officer opens PWA on mobile device.
2. Home screen immediately displays the unit's active tactical assignment card (e.g. `Velachery Rapid Response - Evacuate Zone 4`).
3. Tapping the assignment opens the assignment screen with status progression buttons:
   `ASSIGNED` ➔ `EN_ROUTE` ➔ `ON_SCENE` ➔ `COMPLETED`.
4. Updating status notifies the synchronization queue to transmit state to the Command Center.

---

## 2. On-Scene Incident Reporting
1. Officer encounters new flood conditions or stranded civilians.
2. Taps "Report Incident" from the bottom navigation or quick action tile.
3. Taps **"Acquire GPS"** to fetch high-precision coordinates (`WGS84 EPSG:4326`) and accuracy radius.
   * If GPS is blocked or disabled, toggles **"Manual Coordinate Entry"** to enter latitude and longitude directly.
4. Selects incident severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
5. Inputs descriptive observations and submits.
6. Report is validated against Phase 04 `incident.schema.json` and immediately enqueued.

---

## 3. Evidence Collection
1. Officer captures photographic or video evidence from the "Capture Evidence" screen.
2. Media items are tagged with device coordinates and ISO timestamps.
3. Added to sync queue.

---

## 4. Emergency Resource Requisitions
1. When supplies or tactical equipment run low, officer accesses "Resource Requests".
2. Selects category (`BOAT`, `MEDICAL_KIT`, `WATER_FOOD`, `SANDBAGS`, `PUMP`).
3. Enters quantity, urgency, and operational justification.
4. Request is enqueued.

---

## 5. Severed Network Fallback (SMS Mode)
1. In the event of 100% cellular data / Wi-Fi outage:
2. Officer navigates to **"SMS Fallback"** from the home screen.
3. System encodes incident or mission status into a standard 160-character payload:
   `FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>`
4. Officer taps **"Open in SMS App"** to dispatch message over legacy 2G/GSM networks to the emergency gateway.

---

## 6. Connectivity HUD & Simulation
1. Top bar indicator reflects current connectivity state (`ONLINE`, `OFFLINE`, `SYNCING`, `SYNC_ERROR`).
2. Simulation controls allow field training drills in offline modes.
3. Sync status screen allows officer to monitor queued items and trigger manual synchronization upon regaining signal.
