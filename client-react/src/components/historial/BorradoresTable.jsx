import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Trash2, ChevronRight } from 'lucide-react';

export default function BorradoresTable({ data, onCargar, onEliminar }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Título</TableHead>
          <TableHead>Última modificación</TableHead>
          <TableHead></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((draft) => (
          <TableRow key={draft.id}>
            <TableCell>{draft.titulo}</TableCell>
            <TableCell>{new Date(draft.updated_at).toLocaleDateString()}</TableCell>
            <TableCell className="flex gap-2 justify-end">
              <Button size="sm" onClick={() => onCargar(draft.id)}>Continuar <ChevronRight className="ml-2 h-4 w-4" /></Button>
              <Button size="sm" variant="destructive" onClick={() => onEliminar(draft.id)}><Trash2 className="h-4 w-4" /></Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
