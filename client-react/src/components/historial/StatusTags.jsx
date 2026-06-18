import React from 'react';
import { CheckCircle, XCircle, Clock, FileCheck } from 'lucide-react';
import { cn } from "@/lib/utils";

export const FirmaStatusTag = ({ estado }) => {
  const styles = {
    PENDIENTE_FIRMA: "bg-tertiary-container text-tertiary",
    FIRMADA: "bg-green-100 text-green-700",
    ANULADA: "bg-gray-100 text-gray-500 line-through",
  };

  const labels = {
    PENDIENTE_FIRMA: "Pendiente Firma",
    FIRMADA: "Firmada",
    ANULADA: "Anulada",
  };

  return (
    <span className={cn("px-2 py-1 rounded-full text-xs font-semibold", styles[estado] || "bg-gray-100")}>
      {labels[estado] || estado}
    </span>
  );
};

export const SyncStatusTag = ({ estado, onClick }) => {
  const estadoNormalizado = (estado || "").trim().toLowerCase();

  // 2. Mapeamos también combinaciones comunes por si acaso (ej: exitoso/exitosa)
  const config = {
    exitosa: { icon: CheckCircle, color: "text-green-600", label: "Exitosa" },
    exitoso: { icon: CheckCircle, color: "text-green-600", label: "Exitosa" },
    fallida: { icon: XCircle, color: "text-red-600", label: "Fallida" },
    pendiente: { icon: Clock, color: "text-yellow-600", label: "Pendiente" },
  };

  const { icon: Icon, color, label } = config[estadoNormalizado] || {
    icon: Clock,
    color: "text-gray-500",
    label: estado
  };

  return (
    <div
      className={cn("flex items-center gap-1 text-xs font-medium", color, onClick && "cursor-pointer")}
      onClick={onClick}
      title={estadoNormalizado === 'fallida' ? "Reintentar disponible" : ""}
    >
      <Icon className="h-4 w-4" />
      {label}
    </div>
  );
};

export const PagareTag = ({ tienePagare }) => {
  return tienePagare ? (
    <FileCheck className="h-4 w-4 text-primary/60" />
  ) : (
    <span className="text-muted-foreground">—</span>
  );
};
