/**
 * Configuración centralizada de la API.
 *
 * SaludsaActas está diseñada para vivir exclusivamente en loopback:
 * el frontend se sirve desde el mismo origen que el backend (Flask en
 * producción, Vite proxy en desarrollo). Por eso usamos rutas relativas.
 *
 * NO se permite configurar una URL externa mediante variables de entorno,
 * ya que rompería el modelo de seguridad localhost-only.
 */

export const API_BASE_URL = "";

/**
 * Construye una URL relativa al backend a partir de un path.
 * @param {string} path - path que comienza con /
 * @returns {string}
 */
export function apiUrl(path) {
  if (!path.startsWith("/")) {
    throw new Error(`apiUrl: el path debe comenzar con /. Recibido: ${path}`);
  }
  return `${API_BASE_URL}${path}`;
}
