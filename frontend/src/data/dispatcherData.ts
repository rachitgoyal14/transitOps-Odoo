export const CITIES = [
  { name: 'New Delhi', x: 45, y: 25, region: 'North' },
  { name: 'Jaipur', x: 40, y: 32, region: 'North' },
  { name: 'Mumbai', x: 28, y: 60, region: 'West' },
  { name: 'Pune', x: 30, y: 64, region: 'West' },
  { name: 'Ahmedabad', x: 25, y: 48, region: 'West' },
  { name: 'Bengaluru', x: 42, y: 80, region: 'South' },
  { name: 'Chennai', x: 48, y: 82, region: 'South' },
  { name: 'Hyderabad', x: 44, y: 68, region: 'South' },
  { name: 'Kolkata', x: 78, y: 44, region: 'East' }
];

// Helper to estimate coordinates between two cities at current simulation state
export function getRouteCoordinates(sourceName: string, destName: string) {
  const source = CITIES.find(c => c.name === sourceName);
  const dest = CITIES.find(c => c.name === destName);
  if (!source || !dest) return null;
  return { source, dest };
}

// Distance matrix estimation based on simple coordinate calculation
export function calculateDistance(sourceName: string, destName: string): number {
  if (sourceName === destName) return 0;
  const source = CITIES.find(c => c.name === sourceName);
  const dest = CITIES.find(c => c.name === destName);
  if (!source || !dest) return 0;
  
  // Custom pseudo-distance in miles
  const dx = source.x - dest.x;
  const dy = source.y - dest.y;
  const dist = Math.sqrt(dx*dx + dy*dy) * 22; // multiplier to get realistic highway miles
  return Math.round(dist);
}
