import React from 'react';
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Eraser, Filter } from "lucide-react";

export default function HistorialFiltros({ isOpen, filtros, setFiltros, onAplicar, onLimpiar }) {
  if (!isOpen) return null;

  // Manejador para los checkboxes de estado (permite selección múltiple)
  const toggleEstado = (estadoVal) => {
    const nuevosEstados = filtros.estado.includes(estadoVal)
      ? filtros.estado.filter((e) => e !== estadoVal)
      : [...filtros.estado, estadoVal];
    setFiltros({ ...filtros, estado: nuevosEstados });
  };

  // Manejador genérico para Selects (maneja el caso de "todos" limpiando el valor)
  const handleSelectChange = (field, value) => {
    setFiltros({ ...filtros, [field]: value === "TODOS" ? "" : value });
  };

  return (
    <div className="mb-8 overflow-hidden rounded-xl border border-border bg-background p-6 shadow-sm animate-in slide-in-from-top-4 duration-200">

      {/* Contenedor principal en Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">

        {/* Rango de Fechas */}
        <div className="space-y-3">
          <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Rango de Fechas</Label>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1.5">
              <span className="text-[11px] text-muted-foreground">Desde</span>
              <Input
                type="date"
                className="text-sm"
                value={filtros.fecha_desde || ""}
                onChange={e => setFiltros({ ...filtros, fecha_desde: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <span className="text-[11px] text-muted-foreground">Hasta</span>
              <Input
                type="date"
                className="text-sm"
                value={filtros.fecha_hasta || ""}
                onChange={e => setFiltros({ ...filtros, fecha_hasta: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Tipo de Acta */}
        <div className="space-y-3">
          <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Tipo de Acta</Label>
          <Select
            value={filtros.tipo || "TODOS"}
            onValueChange={(val) => handleSelectChange("tipo", val)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Todos los tipos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODOS">Todos los tipos</SelectItem>
              <SelectItem value="DOTACION">Dotacion</SelectItem>
              <SelectItem value="RENOVACION">Renovacion</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Sincronización YoSoySaludsa */}
        <div className="space-y-3">
          <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">YoSoySaludsa</Label>
          <Select
            value={filtros.sync_status || "TODOS"}
            onValueChange={(val) => handleSelectChange("sync_status", val)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Estado de sincronización" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODOS">Todos</SelectItem>
              <SelectItem value="PENDIENTE">Pendiente</SelectItem>
              <SelectItem value="EXITOSA">Exitosa</SelectItem>
              <SelectItem value="FALLIDA">Fallida</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Pagaré */}
        <div className="space-y-3">
          <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Pagaré Asociado</Label>
          <Select
            value={filtros.tiene_pagare === true ? "SI" : filtros.tiene_pagare === false ? "NO" : "TODOS"}
            onValueChange={(val) => {
              const boolVal = val === "SI" ? true : val === "NO" ? false : "";
              setFiltros({ ...filtros, tiene_pagare: boolVal });
            }}
          >
            <SelectTrigger>
              <SelectValue placeholder="Indiferente" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="TODOS">Indiferente</SelectItem>
              <SelectItem value="SI">Con Pagaré</SelectItem>
              <SelectItem value="NO">Sin Pagaré</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Estado de la Firma (Ocupa el ancho restante en desktop) */}
        <div className="space-y-3 md:col-span-2 lg:col-span-2">
          <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Estado de Firma</Label>
          <div className="flex flex-wrap gap-5 pt-2">
            <label className="flex cursor-pointer items-center gap-2">
              <Checkbox
                checked={filtros.estado.includes('PENDIENTE_FIRMA')}
                onCheckedChange={() => toggleEstado('PENDIENTE_FIRMA')}
              />
              <span className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Pendiente Firma
              </span>
            </label>

            <label className="flex cursor-pointer items-center gap-2">
              <Checkbox
                checked={filtros.estado.includes('FIRMADA')}
                onCheckedChange={() => toggleEstado('FIRMADA')}
              />
              <span className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Firmada
              </span>
            </label>

            <label className="flex cursor-pointer items-center gap-2">
              <Checkbox
                checked={filtros.estado.includes('ANULADA')}
                onCheckedChange={() => toggleEstado('ANULADA')}
              />
              <span className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Anulada
              </span>
            </label>
          </div>
        </div>

      </div>

      {/* Botones de Acción */}
      <div className="mt-8 flex items-center justify-end gap-3 border-t border-border pt-5">
        <Button variant="ghost" size="sm" onClick={onLimpiar} className="text-muted-foreground">
          <Eraser className="mr-2 h-4 w-4" />
          Limpiar filtros
        </Button>
        <Button size="sm" onClick={onAplicar}>
          <Filter className="mr-2 h-4 w-4" />
          Aplicar Filtros
        </Button>
      </div>

    </div>
  );
}
