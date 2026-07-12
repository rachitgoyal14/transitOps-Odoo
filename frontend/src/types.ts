export type TripStatus = 'draft' | 'dispatched' | 'completed' | 'cancelled';
export type VehicleStatus = 'available' | 'on_trip' | 'in_shop' | 'retired';
export type DriverStatus = 'available' | 'on_trip' | 'off_duty' | 'suspended';
export type VehicleType = 'semi' | 'box' | 'van' | string;
export type MaintenanceStatus = 'open' | 'closed';
export type ExpenseCategory = 'toll' | 'parking' | 'repair' | 'insurance' | 'other';
export type ActiveScreen = 'dashboard' | 'trips' | 'fleet' | 'drivers' | 'maintenance' | 'fuel-expenses' | 'analytics' | 'settings';

export interface Vehicle {
  id: string;
  registration_number: string;
  name: string;
  type: string;
  max_load_kg: number;
  odometer_km: number;
  acquisition_cost: number;
  status: VehicleStatus;
  region: string | null;
  lat: number | null;
  lng: number | null;
  depot_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Driver {
  id: string;
  full_name: string;
  license_number: string;
  license_category: string;
  license_expiry: string;
  contact_number: string;
  safety_score: number;
  status: DriverStatus;
  created_at: string;
  updated_at: string;
}

export interface Trip {
  id: string;
  vehicle_id: string;
  driver_id: string;
  source: string;
  destination: string;
  planned_distance_km: number;
  actual_distance_km: number | null;
  cargo_weight_kg: number;
  revenue: number;
  status: TripStatus;
  dispatched_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceLog {
  id: string;
  vehicle_id: string;
  type: string;
  description: string | null;
  cost: number;
  odometer_at_service: number | null;
  status: MaintenanceStatus;
  scheduled_date: string | null;
  completed_date: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface FuelLog {
  id: string;
  vehicle_id: string;
  trip_id: string | null;
  liters: number;
  cost_per_liter: number;
  total_cost: number | null;
  odometer_at_fill: number | null;
  filled_at: string;
  created_at: string;
}

export interface Expense {
  id: string;
  vehicle_id: string;
  trip_id: string | null;
  category: ExpenseCategory;
  amount: number;
  description: string | null;
  expense_date: string;
  created_by: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardMetrics {
  total_vehicles: number;
  available_vehicles: number;
  vehicles_on_trip: number;
  vehicles_in_shop: number;
  vehicles_retired: number;
  fleet_utilization_pct: number;
  active_trips: number;
  pending_trips: number;
  drivers_on_duty: number;
  drivers_available: number;
}

export interface BriefingResponse {
  content: string;
  generated_at: string;
  cached: boolean;
}

export interface FuelEfficiency {
  trip_id: string;
  vehicle_id: string;
  registration_number: string;
  actual_distance_km: number;
  total_liters: number;
  km_per_liter: number;
}

export interface FleetUtilization {
  date: string;
  vehicles_on_trip: number;
  total_active_vehicles: number;
  utilization_pct: number;
}

export interface VehicleCostSummary {
  vehicle_id: string;
  registration_number: string;
  name: string;
  acquisition_cost: number;
  total_fuel_cost: number;
  total_maintenance_cost: number;
  total_operational_cost: number;
  total_revenue: number;
  roi: number | null;
}

export interface FleetLocation {
  vehicle_id: string;
  registration_number: string;
  name: string;
  status: string;
  lat: number | null;
  lng: number | null;
}

export interface AutopilotEvent {
  id: string;
  timestamp: string;
  event_type: string;
  trip_id: string;
  vehicle_id: string | null;
  vehicle_name: string | null;
  driver_id: string | null;
  driver_name: string | null;
  reason: string;
  status: string;
}

export interface AutopilotFeed {
  events: AutopilotEvent[];
  autopilot_enabled: boolean;
  total_dispatched: number;
  total_escalated: number;
}

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}
