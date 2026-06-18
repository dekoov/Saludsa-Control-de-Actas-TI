import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

/**
 * Componente Wrapper para proteger rutas que requieren autenticación.
 * - Muestra un spinner si está cargando el estado inicial.
 * - Redirige a /login si no está autenticado.
 * - Renderiza los hijos si está autenticado.
 */
export const RutaProtegida = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center space-y-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
        <p className="text-sm font-medium text-muted-foreground">Verificando sesión...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirigir a login, guardando la ubicación actual para volver después si se desea
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};
