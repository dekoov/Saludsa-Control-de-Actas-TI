/**
 * Wrapper de fetch para asegurar que todas las peticiones al backend
 * incluyan las cookies de sesión (credentials: "include") y manejen
 * automáticamente los errores de autenticación (401).
 */
export async function fetchConAuth(url, options = {}) {
  // Aseguramos que las credenciales se incluyan siempre
  const defaultOptions = {
    ...options,
    credentials: "include",
    headers: {
      "Accept": "application/json",
      ...(options.headers || {}),
    },
  };

  try {
    const response = await fetch(url, defaultOptions);

    // Si el servidor retorna 401 (No autorizado), limpiamos la sesión local
    if (response.status === 401) {
      console.warn("[Auth] Sesión expirada o no válida. Redirigiendo a login...");
      
      // Emitir un evento personalizado para que AuthContext pueda reaccionar
      window.dispatchEvent(new CustomEvent("auth-unauthorized"));
      
      // Opcional: Redirigir directamente si no estamos ya en login
      if (!window.location.hash.includes("/login")) {
         window.location.hash = "/login";
      }
    }

    return response;
  } catch (error) {
    console.error("[fetchConAuth] Error de red:", error);
    throw error;
  }
}
