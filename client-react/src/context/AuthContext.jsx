import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { fetchConAuth } from "@/lib/fetchConAuth";

const AuthContext = createContext(null);

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:5000";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkAuthStatus = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/auth/estado`);
      const result = await response.json();

      if (result.status && result.data?.autenticado) {
        setUser(result.data.tecnico);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (err) {
      console.error("[AuthContext] Error verificando estado:", err);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuthStatus();

    // Escuchar eventos de desautenticación global (de fetchConAuth)
    const handleUnauthorized = () => {
      setUser(null);
      setIsAuthenticated(false);
    };

    window.addEventListener("auth-unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth-unauthorized", handleUnauthorized);
  }, [checkAuthStatus]);

  const login = async (username, password) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchConAuth(`${BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();

      if (response.ok && result.status) {
        setUser(result.data);
        setIsAuthenticated(true);
        return { success: true };
      } else {
        const msg = result.message || "Error al iniciar sesión";
        setError(msg);
        return { success: false, message: msg };
      }
    } catch (err) {
      const msg = "No se pudo conectar con el servidor";
      setError(msg);
      return { success: false, message: msg };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await fetchConAuth(`${BASE_URL}/api/auth/logout`, { method: "POST" });
    } catch (err) {
      console.error("[AuthContext] Error al cerrar sesión:", err);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      window.location.hash = "/login";
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        error,
        login,
        logout,
        checkAuthStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
};
