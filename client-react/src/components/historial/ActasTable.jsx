import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FirmaStatusTag, SyncStatusTag, PagareTag } from './StatusTags';
import ActaRowMenu from './ActaRowMenu';

export default function ActasTable({ data, columnasVisibles, onRefreshRequired }) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground bg-gray-50/50 rounded-lg border border-dashed">
        No hay actas generadas para mostrar.
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Fecha & ID</TableHead>
          <TableHead>Usuario</TableHead>
          <TableHead>Equipo Principal</TableHead>
          {columnasVisibles?.accesorios && <TableHead>Accesorios</TableHead>}
          <TableHead>Estado Firma</TableHead>
          {columnasVisibles?.sync && <TableHead>Sync Saludsa</TableHead>}
          {columnasVisibles?.pagare && <TableHead>Pagaré</TableHead>}
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((acta) => {
          const usuarioActa = acta?.empleado || acta?.usuario || {};
          const fechaValida = acta?.fecha ? new Date(acta.fecha).toLocaleDateString() : "N/A";

          {/* Parche debido que no hay un estado consultado al backend */ }
          const syncStatusNormalizado = acta?.estado_sincronizacion && acta.estado_sincronizacion.trim() !== ""
            ? acta.estado_sincronizacion.toLowerCase()
            : "pendiente";

          return (
            <TableRow key={acta?.id || Math.random()}>
              <TableCell className="align-top">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-foreground">{fechaValida}</span>
                  <span className="text-[11px] text-muted-foreground mt-0.5 uppercase tracking-wider">
                    {acta?.id || "N/A"}
                  </span>
                </div>
              </TableCell>

              <TableCell className="align-top">
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-foreground">
                    {usuarioActa.full_name || "Usuario Desconocido"}
                  </span>
                  <span className="text-[11px] text-muted-foreground mt-0.5">
                    {usuarioActa.username || ""}
                  </span>
                </div>
              </TableCell>

              <TableCell className="align-top">
                {acta?.equipos_resumen && acta.equipos_resumen !== "Sin equipo principal" ? (
                  <div className="flex flex-col gap-2">
                    {acta.equipos_resumen.split(' / ').map((equipo, idx) => {
                      const parts = equipo.split(' | ');
                      const modelo = parts.pop();
                      const meta = parts.join(' • ');

                      return (
                        <div key={idx} className="flex flex-col">
                          <span className="text-sm font-medium text-foreground">{modelo || "Equipo"}</span>
                          {meta && <span className="text-[11px] text-muted-foreground mt-0.5">{meta}</span>}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <span className="text-sm text-muted-foreground italic">No especificado</span>
                )}
              </TableCell>

              {columnasVisibles?.accesorios && (
                <TableCell className="align-top">
                  <span className="bg-gray-100 px-2 py-1 rounded-full text-xs">
                    {acta?.accesorios_resumen || "Ninguno"}
                  </span>
                </TableCell>
              )}

              <TableCell className="align-top">
                <FirmaStatusTag estado={acta?.estado || "DESCONOCIDO"} />
              </TableCell>

              {columnasVisibles?.sync && (
                <TableCell className="align-top">
                  {/* Se renderiza el tag con el estado normalizado */}
                  <SyncStatusTag estado={syncStatusNormalizado} />
                </TableCell>
              )}

              {columnasVisibles?.pagare && (
                <TableCell className="align-top">
                  <PagareTag tienePagare={!!acta?.tiene_pagare} />
                </TableCell>
              )}

              <TableCell className="align-top">
                <ActaRowMenu
                  // Le pasamos el acta al menú con el estado de sincronización normalizado
                  acta={{ ...acta, estado_sincronizacion: syncStatusNormalizado }}
                  onActionSuccess={onRefreshRequired}
                />
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
