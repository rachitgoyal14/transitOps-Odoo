import type { Vehicle, Driver, Trip, MaintenanceLog } from '../types';

// Backend returns snake_case / different field names.
// These adapters transform API data into the shape existing components expect.

export interface AdaptedVehicle extends Vehicle {
  capacity: number;
  currentOdometer: number;
  acquisitionCost: number;
}

export interface AdaptedDriver extends Driver {
  name: string;
  licenseNo: string;
  category: string;
  expiry: string;
  contact: string;
  tripCompliance: number;
  safetyScore: number;
}

export interface AdaptedTrip extends Trip {
  vehicleId: string;
  driverId: string;
  cargoWeight: number;
  distance: number;
  eta: string;
}

export function adaptVehicle(v: Vehicle): AdaptedVehicle {
  return {
    ...v,
    capacity: v.max_load_kg,
    currentOdometer: v.odometer_km,
    acquisitionCost: v.acquisition_cost,
  };
}

export function adaptDriver(d: Driver): AdaptedDriver {
  return {
    ...d,
    name: d.full_name,
    licenseNo: d.license_number,
    category: d.license_category,
    expiry: d.license_expiry?.split('T')[0] || '',
    contact: d.contact_number,
    tripCompliance: 95,
    safetyScore: d.safety_score,
  };
}

export function adaptTrip(t: Trip): AdaptedTrip {
  const now = new Date();
  let eta = '--';
  if (t.status === 'dispatched' && t.dispatched_at) {
    const elapsed = Math.floor((now.getTime() - new Date(t.dispatched_at).getTime()) / 60000);
    const remaining = Math.max(0, 480 - elapsed);
    const h = Math.floor(remaining / 60);
    const m = remaining % 60;
    eta = remaining > 0 ? `${h}h ${String(m).padStart(2, '0')}m` : 'Overdue';
  } else if (t.status === 'completed') {
    eta = 'Completed';
  } else if (t.status === 'cancelled') {
    eta = 'Cancelled';
  }

  return {
    ...t,
    vehicleId: t.vehicle_id,
    driverId: t.driver_id,
    cargoWeight: t.cargo_weight_kg,
    distance: t.planned_distance_km,
    eta,
  };
}

export function adaptMaintenanceLog(m: MaintenanceLog) {
  return {
    id: m.id,
    vehicleId: m.vehicle_id,
    serviceType: m.type,
    cost: m.cost,
    date: m.scheduled_date?.split('T')[0] || m.created_at.split('T')[0],
    status: m.status === 'open' ? ('active' as const) : ('closed' as const),
    description: m.description || '',
    odometerAtService: m.odometer_at_service,
    completedDate: m.completed_date,
  };
}

// Reverse adapters: convert component form data back to API shape

export function toVehiclePayload(data: Record<string, unknown>) {
  const payload: Record<string, unknown> = {};
  if (data.id) payload.registration_number = data.id;
  if (data.name) payload.name = data.name;
  if (data.type) payload.type = data.type;
  if (data.capacity !== undefined) payload.max_load_kg = data.capacity;
  if (data.currentOdometer !== undefined) payload.odometer_km = data.currentOdometer;
  if (data.acquisitionCost !== undefined) payload.acquisition_cost = data.acquisitionCost;
  if (data.status) payload.status = data.status;
  return payload;
}

export function toDriverPayload(data: Record<string, unknown>) {
  const payload: Record<string, unknown> = {};
  if (data.name) payload.full_name = data.name;
  if (data.licenseNo) payload.license_number = data.licenseNo;
  if (data.category) payload.license_category = data.category;
  if (data.expiry) payload.license_expiry = data.expiry;
  if (data.contact) payload.contact_number = data.contact;
  if (data.safetyScore !== undefined) payload.safety_score = data.safetyScore;
  if (data.status) payload.status = data.status;
  return payload;
}

export function toTripPayload(data: Record<string, unknown>) {
  const payload: Record<string, unknown> = {};
  if (data.source) payload.source = data.source;
  if (data.destination) payload.destination = data.destination;
  if (data.vehicleId) payload.vehicle_id = data.vehicleId;
  if (data.driverId) payload.driver_id = data.driverId;
  if (data.cargoWeight !== undefined) payload.cargo_weight_kg = data.cargoWeight;
  if (data.distance !== undefined) payload.planned_distance_km = data.distance;
  if (data.revenue !== undefined) payload.revenue = data.revenue;
  if (data.notes) payload.notes = data.notes;
  return payload;
}

// Map backend role names to frontend role IDs
const ROLE_MAP: Record<string, string> = {
  fleet_manager: 'manager',
  dispatcher: 'dispatcher',
  safety_officer: 'safety',
  financial_analyst: 'finance',
};

export function mapRole(backendRole: string): string {
  return ROLE_MAP[backendRole] || 'admin';
}
