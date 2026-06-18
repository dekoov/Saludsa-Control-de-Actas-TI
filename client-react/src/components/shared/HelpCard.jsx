import { Download } from "lucide-react";

export default function HelpCard() {
  return (
    <div className="mt-6 rounded-2xl bg-primary p-5 text-primary-foreground shadow-sm">
      <h3 className="text-base font-bold">
        ¿Necesitas ayuda con el registro?
      </h3>
      <p className="mt-1 text-sm text-primary-foreground/80">
        Consulta la guía rápida de digitalización de actas para el
        sistema YoSoySaludsa.
      </p>
      <button className="mt-4 inline-flex items-center gap-2 rounded-full bg-background px-4 py-2 text-sm font-semibold text-primary transition hover:bg-background/90">
        <Download className="h-4 w-4" />
        Descargar PDF
      </button>
    </div>
  );
}
