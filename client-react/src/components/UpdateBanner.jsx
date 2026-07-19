import { Download, RefreshCw, Loader2, AlertCircle } from "lucide-react";
import { useUpdateCheck } from "@/hooks/useUpdateCheck";

const STAGE_LABELS = {
  downloading: "Descargando actualización",
  verifying: "Verificando integridad del instalador",
  restarting: "Instalación lista. Reiniciando la aplicación...",
};

export default function UpdateBanner() {
  const {
    updateAvailable,
    latestVersion,
    currentVersion,
    applying,
    progress,
    stage,
    error,
    applyUpdate,
  } = useUpdateCheck();

  if (!updateAvailable && !applying) return null;

  const stageLabel = STAGE_LABELS[stage] || "Procesando actualización";

  return (
    <div className="mb-6 rounded-xl border border-primary/30 bg-primary/5 px-5 py-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Download className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">
              Nueva versión disponible: v{latestVersion}
            </p>
            <p className="text-xs text-muted-foreground">
              {applying
                ? stageLabel
                : `Tienes la v${currentVersion}. La aplicación se reiniciará para actualizarse.`}
            </p>
          </div>
        </div>

        {!applying && (
          <button
            onClick={applyUpdate}
            className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition hover:bg-primary/90"
          >
            {error ? (
              <RefreshCw className="h-4 w-4" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            {error ? "Reintentar" : "Actualizar ahora"}
          </button>
        )}

        {applying && stage !== "restarting" && (
          <div className="flex items-center gap-2 text-sm font-medium text-primary">
            <Loader2 className="h-4 w-4 animate-spin" />
            {stage === "downloading" && progress !== null
              ? `${progress}%`
              : "Procesando..."}
          </div>
        )}

        {applying && stage === "restarting" && (
          <div className="flex items-center gap-2 text-sm font-medium text-primary">
            <Loader2 className="h-4 w-4 animate-spin" />
            Reiniciando...
          </div>
        )}
      </div>

      {applying && stage === "downloading" && progress !== null && (
        <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-primary/20">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {error && !applying && (
        <div className="mt-3 flex items-center gap-2 text-xs text-destructive">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}
    </div>
  );
}
