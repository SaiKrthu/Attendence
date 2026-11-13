export function getMapUrl(latitude: number, longitude: number): string {
  const coordinates = encodeURIComponent(`${latitude},${longitude}`);
  return `https://www.google.com/maps/search/?api=1&query=${coordinates}`;
}
