import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { IncidentsPage } from '../IncidentsPage';
import { AppProvider } from '../../context/AppContext';

describe('IncidentsPage Operational Management', () => {
  it('renders Incident Dispatch Roster and permits status transitions', () => {
    render(<AppProvider><IncidentsPage /></AppProvider>);

    expect(screen.getByText('Operational Incident Management')).toBeDefined();
    expect(screen.getByText('Incident Dispatch Roster')).toBeDefined();

    // Inspect first incident
    const inspectButtons = screen.getAllByText('Inspect');
    expect(inspectButtons.length).toBeGreaterThan(0);
    fireEvent.click(inspectButtons[0]);

    // Check detail inspector opens with lifecycle actions
    expect(screen.getByText(/PERMITTED LIFECYCLE ACTIONS:/i)).toBeDefined();

    // Transition action (Acknowledge)
    const ackButton = screen.getByText('✓ Acknowledge');
    fireEvent.click(ackButton);

    // Verify status updated and next allowed lifecycle action appears
    expect(screen.getByText('▶ Start Response')).toBeDefined();
  });

  it('allows opening incident registration form, enforces description validation, and adds to roster', () => {
    render(<AppProvider><IncidentsPage /></AppProvider>);

    const reportButton = screen.getByText('＋ Report Incident');
    fireEvent.click(reportButton);

    expect(screen.getByText('Register New Emergency Incident')).toBeDefined();

    // Attempt submit with empty description
    const submitButton = screen.getByText('Submit Operational Report');
    fireEvent.click(submitButton);

    expect(screen.getByText('Situational description is required.')).toBeDefined();

    // Fill description and submit
    const textarea = screen.getByPlaceholderText(/Describe emergency conditions/i);
    fireEvent.change(textarea, { target: { value: 'Flash inundation at crossing' } });
    fireEvent.click(submitButton);

    // Form closes and new incident is selected
    expect(screen.getByText(/Situation Report:/i)).toBeDefined();
    expect(screen.getByText('Flash inundation at crossing')).toBeDefined();
  });
});
