import { useState, useEffect, useCallback, useRef } from "react";
import { fetchConAuth } from "@/lib/fetchConAuth";

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:5000";

const POLL_NORMAL_MS = 5 * 60 * 1000; // Cada 5 minutos en reposo
const POLL_APPLYING_MS = 1000;        // Cada segundo mientras se actualiza
const MAX_NETWORK_FAILURES = 3;       // Fallos seguidos antes de asumir cierre del backend

/**
 * Hook que consulta el estado de actualización de la aplicación.
 * - Al cargar y cada 5 min consulta GET /api/system/version.
 * - Mientras hay una actualización en curso (applying), consulta cada 1s
 *   para reflejar el progreso de descarga en tiempo casi real.
 * - Los errores de red son silenciosos, EXCEPTO durante una actualización:
 *   si el backend deja de responder mientras applying=true, se interpreta
 *   como el cierre esperado del servidor para instalar la nueva versión
 *   (el updater desacoplado instala y reabre la app). En ese caso la UI
 *   pasa a stage "restarting" sin marcar error.
 * - Cuando el backend vuelve a responder tras ese cierre, la página se
 *   recarga una sola vez para cargar los assets de la versión recién
 *   instalada (evita usar un frontend viejo contra un backend nuevo).
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
  const failCountRef = useRef(0);
  const backendDownRef = useRef(false);
  const reloadedRef = useRef(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/system/version`);
      if (!response.ok) return;

      const result = await response.json();
      const d = result.data || {};
      failCountRef.current = 0;

      // El backend estuvo caído durante la actualización y ahora responde:
      // la app ya se reinstaló y reabrió. Recargar una sola vez para cargar
      // los assets de la versión nueva (si la instalación falló y volvió la
      // versión anterior, el reload es inofensivo y el banner reaparece solo).
      if (backendDownRef.current && applyingRef.current) {
        if (!reloadedRef.current) {
          reloadedRef.current = true;
          window.location.reload();
        }
        return;
      }
      backendDownRef.current = false;
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
      // Fuera de una actualización, los errores de red son silenciosos.
      if (!applyingRef.current) return;

      // Durante una actualización, exigir varios fallos consecutivos antes de
      // interpretar que el backend se cerró para instalar (evita falsos
      // positivos por parpadeos de red mientras dura la descarga).
      failCountRef.current += 1;
      if (failCountRef.current < MAX_NETWORK_FAILURES) return;

      backendDownRef.current = true;
      setState((s) => {
        // Guarda: si ya estamos en "restarting", no re-renderizar cada 1s.
        if (s.applying && s.stage === "restarting") return s;
        return { ...s, applying: true, stage: "restarting", progress: 100, error: null };
      });
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
    failCountRef.current = 0;
    backendDownRef.current = false;
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
