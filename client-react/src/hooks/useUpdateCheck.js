import { useState, useEffect, useCallback, useRef } from "react";
import { fetchConAuth } from "@/lib/fetchConAuth";

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:5000";

const POLL_NORMAL_MS = 5 * 60 * 1000; // Cada 5 minutos en reposo
const POLL_APPLYING_MS = 1000;        // Cada segundo mientras se actualiza

/**
 * Hook que consulta el estado de actualización de la aplicación.
 * - Al cargar y cada 5 min consulta GET /api/system/version.
 * - Mientras hay una actualización en curso (applying), consulta cada 1s
 *   para reflejar el progreso de descarga en tiempo casi real.
 * - Los errores de red son silenciosos.
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

  const applyingRef = useRef(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/system/version`);
      if (!response.ok) return;

      const result = await response.json();
      const d = result.data || {};
      applyingRef.current = Boolean(d.applying);

      setState({
        currentVersion: d.current_version ?? null,
        updateAvailable: Boolean(d.update_available),
        latestVersion: d.latest_version ?? null,
        applying: Boolean(d.applying),
        progress: d.progress ?? null,
        stage: d.stage ?? null,
        error: d.error ?? null,
      });
    } catch {
      // Errores de red silenciosos: no interrumpir al usuario
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
    };
  }, [fetchStatus, state.applying]);

  const applyUpdate = useCallback(async () => {
    applyingRef.current = true;
    setState((s) => ({ ...s, applying: true, error: null, stage: "downloading" }));
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/system/update/apply`, {
        method: "POST",
      });
      const result = await response.json();

      if (!response.ok || !result.status) {
        applyingRef.current = false;
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
      applyingRef.current = false;
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
