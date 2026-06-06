const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? '';

export const apiBaseUrl = rawApiBaseUrl.replace(/\/+$/, '');

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  if (!apiBaseUrl) {
    return normalizedPath;
  }

  return `${apiBaseUrl}${normalizedPath}`;
}
