import type {
  Vehicle, Driver, Trip, MaintenanceLog, FuelLog, Expense,
  PaginatedResponse, DashboardMetrics, BriefingResponse,
  FuelEfficiency, FleetUtilization, VehicleCostSummary,
  FleetLocation, AutopilotFeed, User
} from '../types';

const BASE = '/api/v1';

function getToken(): string | null {
  return localStorage.getItem('auth_token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (res.status === 204) return null as T;

  const body = await res.json();
  if (!res.ok) {
    const msg = typeof body?.detail === 'string' ? body.detail : JSON.stringify(body);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return body as T;
}

// ── Auth ────────────────────────────────────────────────────────────────

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form.toString(),
  });
  if (!res.ok) {
    const body = await res.json();
    throw new Error(body.detail || 'Login failed');
  }
  return res.json() as Promise<{ access_token: string; token_type: string }>;
}

export async function getMe() {
  return request<User>('/auth/me');
}

// ── Vehicles ────────────────────────────────────────────────────────────

export async function listVehicles(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<Vehicle>>(`/vehicles/${qs}`);
}

export async function getVehicle(id: string) {
  return request<Vehicle>(`/vehicles/${id}`);
}

export async function getAvailableVehicles() {
  return request<Vehicle[]>('/vehicles/available');
}

export async function createVehicle(data: Partial<Vehicle>) {
  return request<Vehicle>('/vehicles/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateVehicle(id: string, data: Partial<Vehicle>) {
  return request<Vehicle>(`/vehicles/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function deleteVehicle(id: string) {
  return request<Vehicle>(`/vehicles/${id}`, { method: 'DELETE' });
}

export async function getVehicleCostSummary(id: string) {
  return request<VehicleCostSummary>(`/vehicles/${id}/cost-summary`);
}

// ── Drivers ─────────────────────────────────────────────────────────────

export async function listDrivers(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<Driver>>(`/drivers/${qs}`);
}

export async function getDriver(id: string) {
  return request<Driver>(`/drivers/${id}`);
}

export async function getAvailableDrivers() {
  return request<Driver[]>('/drivers/available');
}

export async function getExpiringLicenses() {
  return request<Driver[]>('/drivers/expiring-licenses');
}

export async function createDriver(data: Partial<Driver>) {
  return request<Driver>('/drivers/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateDriver(id: string, data: Partial<Driver>) {
  return request<Driver>(`/drivers/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function deleteDriver(id: string) {
  return request<Driver>(`/drivers/${id}`, { method: 'DELETE' });
}

// ── Trips ───────────────────────────────────────────────────────────────

export async function listTrips(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<Trip>>(`/trips${qs}`);
}

export async function getTrip(id: string) {
  return request<Trip>(`/trips/${id}`);
}

export async function createTrip(data: Record<string, unknown>) {
  return request<Trip>('/trips/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateTrip(id: string, data: Record<string, unknown>) {
  return request<Trip>(`/trips/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function dispatchTrip(id: string) {
  return request<Trip>(`/trips/${id}/dispatch`, { method: 'POST' });
}

export async function completeTrip(id: string, data: Record<string, unknown>) {
  return request<Trip>(`/trips/${id}/complete`, { method: 'POST', body: JSON.stringify(data) });
}

export async function cancelTrip(id: string, reason: string) {
  return request<Trip>(`/trips/${id}/cancel`, { method: 'POST', body: JSON.stringify({ reason }) });
}

export async function suggestDispatch(data: Record<string, unknown>) {
  return request<{ suggestions: Array<{ rank: number; vehicle_id: string; vehicle_name: string; driver_id: string; driver_name: string; reason: string }>; excluded: string }>('/trips/suggest', { method: 'POST', body: JSON.stringify(data) });
}

// ── Maintenance ─────────────────────────────────────────────────────────

export async function listMaintenance(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<MaintenanceLog>>(`/maintenance/${qs}`);
}

export async function getMaintenanceLog(id: string) {
  return request<MaintenanceLog>(`/maintenance/${id}`);
}

export async function createMaintenanceLog(data: Record<string, unknown>) {
  return request<MaintenanceLog>('/maintenance/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateMaintenanceLog(id: string, data: Record<string, unknown>) {
  return request<MaintenanceLog>(`/maintenance/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function closeMaintenanceLog(id: string, data: Record<string, unknown>) {
  return request<MaintenanceLog>(`/maintenance/${id}/close`, { method: 'POST', body: JSON.stringify(data) });
}

// ── Fuel Logs ───────────────────────────────────────────────────────────

export async function listFuelLogs(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<FuelLog>>(`/fuel-logs/${qs}`);
}

export async function createFuelLog(data: Record<string, unknown>) {
  return request<FuelLog>('/fuel-logs/', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteFuelLog(id: string) {
  return request<void>(`/fuel-logs/${id}`, { method: 'DELETE' });
}

// ── Expenses ────────────────────────────────────────────────────────────

export async function listExpenses(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<PaginatedResponse<Expense>>(`/expenses/${qs}`);
}

export async function createExpense(data: Record<string, unknown>) {
  return request<Expense>('/expenses/', { method: 'POST', body: JSON.stringify(data) });
}

export async function deleteExpense(id: string) {
  return request<void>(`/expenses/${id}`, { method: 'DELETE' });
}

// ── Dashboard ───────────────────────────────────────────────────────────

export async function getDashboardMetrics(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<DashboardMetrics>(`/dashboard${qs}`);
}

export async function getActiveTrips() {
  return request<Trip[]>('/dashboard/active-trips');
}

export async function getBriefing() {
  return request<BriefingResponse>('/dashboard/briefing', { method: 'POST' });
}

// ── Reports ─────────────────────────────────────────────────────────────

export async function getFuelEfficiency(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<FuelEfficiency[]>(`/reports/fuel-efficiency${qs}`);
}

export async function getFleetUtilization(params?: Record<string, string>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<FleetUtilization[]>(`/reports/fleet-utilization${qs}`);
}

export async function getOperationalCost() {
  return request<VehicleCostSummary[]>(`/reports/operational-cost`);
}

export async function getVehicleROI() {
  return request<VehicleCostSummary[]>(`/reports/vehicle-roi`);
}

export async function downloadCSV(report: string) {
  const token = getToken();
  const res = await fetch(`${BASE}/reports/export/csv?report=${report}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error('CSV export failed');
  return res.blob();
}

// ── Fleet Map ───────────────────────────────────────────────────────────

export async function getFleetLocations() {
  return request<FleetLocation[]>('/fleet/locations');
}

// ── Autopilot ───────────────────────────────────────────────────────────

export async function toggleAutopilot(enabled: boolean) {
  return request<{ enabled: boolean; message: string }>('/trips/autopilot/toggle', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });
}

export async function getAutopilotFeed() {
  return request<AutopilotFeed>('/trips/autopilot/feed');
}

// ── User Management ─────────────────────────────────────────────────────

export async function createUser(data: { full_name: string; email: string; password: string; role: string }) {
  return request<User>('/auth/users', { method: 'POST', body: JSON.stringify(data) });
}

// ── Chat ────────────────────────────────────────────────────────────────

export async function askChat(question: string) {
  return request<{ answer: string }>('/chat/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}
