import { useState, useEffect, useCallback, useRef } from "react";
import { fetchConAuth } from "@/lib/fetchConAuth";

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:5000";

const POLL_NORMAL_MS = 5 * 60 * 1000;   // Cada 5 minutos en reposo
const POLL_APPLYING_MS = 1000;          // Cada segundo mientras se actualiza
const STUCK_TIMEOUT_MS = 90 * 1000;     // Si sigue "applying" pasado esto, avisar

/**
 * Hook que consulta el estado de actualización de la aplicación.
 * - Al cargar y cada 5 min consulta GET /api/system/version.
 * - Mientras hay una actualización en curso (applying), consulta cada 1s
 *   para reflejar el progreso de descarga en tiempo casi real.
 * - Durante el reinicio real, el server Flask muere y la ventana queda
 *   pegada al mismo localhost esperando que vuelva a responder. Mientras
 *   eso pasa, cada poll falla -- si el último estado conocido era
 *   "applying", se fuerza stage:"restarting" en vez de congelar la UI en
 *   el último snapshot visto (que puede ser "downloading" o "verifying").
 * - Si "applying" sigue true después de STUCK_TIMEOUT_MS sin resolverse,
 *   se muestra un error explícito en vez de un spinner infinito.
 */
export function useUpdateCheck() {
  const [state, setState] = useState({
    currentVersion: null,
    updateAvailable: false,
    latestVersion: null,
    applying: false,
    progress: null,
    stage: null,
    error: null,
  });

  const stuckTimeoutRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/system/version`);
      if (!response.ok) return;
      const result = await response.json();
      const d = result.data || {};

      setState({
        currentVersion: d.current_version ?? null,
        updateAvailable: Boolean(d.update_available),
        latestVersion: d.latest_version ?? null,
        applying: Boolean(d.applying),
        progress: d.progress ?? null,
        stage: d.stage ?? null,
        error: d.error ?? null,
      });

      if (d.applying) {
        // Cada respuesta exitosa reinicia el reloj de "esto se colgó".
        clearTimeout(stuckTimeoutRef.current);
        stuckTimeoutRef.current = setTimeout(() => {
          setState((s) => ({
            ...s,
            error:
              "La actualización está tardando más de lo esperado. " +
              "Revisá logs/updater.log o reiniciá la aplicación manualmente.",
          }));
        }, STUCK_TIMEOUT_MS);
      } else {
        clearTimeout(stuckTimeoutRef.current);
      }
    } catch {
      // El server cae durante el reinicio real -- eso es esperado.
      // Si veníamos de "applying", asumimos que sigue reiniciando en vez
      // de congelar la UI en el último stage que se llegó a ver.
      setState((s) => (s.applying ? { ...s, stage: "restarting" } : s));
    }
  }, []);

  useEffect(() => {
    // Diferido para no llamar setState de forma síncrona dentro del efecto
    const initial = setTimeout(fetchStatus, 0);
    const interval = setInterval(
      fetchStatus,
      state.applying ? POLL_APPLYING_MS : POLL_NORMAL_MS
    );
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
      clearTimeout(stuckTimeoutRef.current);
    };
  }, [fetchStatus, state.applying]);

  const applyUpdate = useCallback(async () => {
    setState((s) => ({ ...s, applying: true, error: null, stage: "downloading" }));
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/system/update/apply`, {
        method: "POST",
      });
      const result = await response.json();
      if (!response.ok || !result.status) {
        setState((s) => ({
          ...s,
          applying: false,
          stage: null,
          error: result.message || "No se pudo iniciar la actualización",
        }));
        return false;
      }
      return true;
    } catch {
      setState((s) => ({
        ...s,
        applying: false,
        stage: null,
        error: "Error de red al iniciar la actualización",
      }));
      return false;
    }
  }, []);

  return { ...state, applyUpdate, refresh: fetchStatus };
}
