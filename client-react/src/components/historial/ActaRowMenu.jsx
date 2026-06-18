import React, { useState } from 'react';
import { MoreHorizontal, FileText, CheckCircle, RefreshCw, Trash2, Loader2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  downloadActaDocumentPDF,
  marcarActaComoFirmada,
  reintentarSyncActa,
  anularActa
} from "@/lib/api";

export default function ActaRowMenu({ acta, onActionSuccess }) {
  const [loadingAction, setLoadingAction] = useState(null);

  const executeAction = async (actionType, apiCall, successMessage, stateUpdates = null) => {
    setLoadingAction(actionType);
    try {
      await apiCall();
      if (successMessage) {
        toast.success(successMessage);
      }
      // Mandamos al padre qué acta cambió y qué campos se alteraron
      if (onActionSuccess) {
        onActionSuccess(acta.id, stateUpdates);
      }
    } catch (err) {
      toast.error(err.message || "Ocurrió un error inesperado al procesar la solicitud.");
    } finally {
      setLoadingAction(null);
    }
  };

  // Buscaremos si la sincronización está fallida o vacía (Pendiente) para habilitar el botón
  const syncLower = (acta.estado_sincronizacion || "").toLowerCase();

  const puedeSincronizar =
    syncLower === 'fallida' ||
    syncLower === 'pendiente' ||
    !acta.estado_sincronizacion;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0" disabled={loadingAction !== null}>
          {loadingAction ? (
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
          ) : (
            <MoreHorizontal className="h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="rounded-2xl w-52">
        <DropdownMenuItem
          onSelect={() => executeAction('acta', () => downloadActaDocumentPDF(acta.id, 'acta'))}
        >
          <FileText className="mr-2 h-4 w-4" /> Descargar Acta
        </DropdownMenuItem>

        <DropdownMenuItem
          disabled={!acta.tiene_pagare}
          onSelect={() => executeAction('pagare', () => downloadActaDocumentPDF(acta.id, 'pagare'))}
        >
          <FileText className="mr-2 h-4 w-4" /> Descargar Pagaré
        </DropdownMenuItem>

        <DropdownMenuItem
          disabled={acta.estado !== 'PENDIENTE_FIRMA'}
          onSelect={() => executeAction(
            'firmar',
            () => marcarActaComoFirmada(acta.id),
            "Acta marcada como firmada",
            { estado: 'FIRMADA' } // <- Inyección de cambio de estado
          )}
        >
          <CheckCircle className="mr-2 h-4 w-4" /> Marcar como Firmada
        </DropdownMenuItem>

        <DropdownMenuItem
          disabled={!puedeSincronizar}
          onSelect={() => executeAction(
            'sync',
            () => reintentarSyncActa(acta.id),
            "Sincronización reintentada exitosamente",
            { estado_sincronizacion: 'exitoso' } // <- Se asume éxito inicial tras disparar
          )}
        >
          <RefreshCw className="mr-2 h-4 w-4" /> Reintentar Sync
        </DropdownMenuItem>

        <div className="h-px bg-border my-1" />

        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          disabled={acta.estado === 'ANULADA'}
          onSelect={(e) => {
            e.preventDefault();
            if (window.confirm(`¿Está seguro de anular el acta ${acta.id}? Esta operación es irreversible.`)) {
              executeAction(
                'anular',
                () => anularActa(acta.id),
                "El acta ha sido anulada",
                { estado: 'ANULADA' } // <- Al anular, cambia el tag de la firma a ANULADA
              );
            }
          }}
        >
          <Trash2 className="mr-2 h-4 w-4" /> Anular Acta
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
