import React, { useState, useEffect } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function HistorialSearch({ onSearch, filtrosActivosCount, toggleFiltros }) {
  const [value, setValue] = useState("");

  useEffect(() => {
    const handler = setTimeout(() => {
      onSearch(value);
    }, 400);

    return () => clearTimeout(handler);
  }, [value, onSearch]);

  return (
    <div className="flex items-center gap-2 mb-8">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Buscar por ID de acta, nombre, usuario, hostname, número de serie, modelo o marca"
          className="pl-9 h-12 rounded-2xl border-outline_variant/20 focus-visible:ring-primary"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </div>
      <Button
        variant="outline"
        className="h-12 rounded-2xl gap-2 border-outline_variant/20"
        onClick={toggleFiltros}
      >
        <SlidersHorizontal className="h-4 w-4" />
        Filtros {filtrosActivosCount > 0 && <span className="bg-primary text-primary-foreground rounded-full px-2 py-0.5 text-xs">{filtrosActivosCount}</span>}
      </Button>
    </div>
  );
}
