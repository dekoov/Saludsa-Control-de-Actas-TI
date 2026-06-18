import {
  ArrowRight,
  FileText,
  Mail,
  RefreshCw,
  ShieldCheck,
  Check,
  Loader2,
  Circle,
  XCircle,
  Save,
} from "lucide-react";

function Row({ label, value, muted }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border/60 pb-2 last:border-0 last:pb-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd
        className={`max-w-[55%] truncate text-right font-semibold ${muted ? "text-muted-foreground" : "text-foreground"
          }`}
      >
        {value}
      </dd>
    </div>
  );
}

function Task({ icon, label, state }) {
  const tone =
    state === "done"
      ? "text-foreground"
      : state === "error"
        ? "text-destructive font-medium"
        : state === "running"
          ? "text-foreground"
          : "text-muted-foreground/70";
  const bullet =
    state === "done" ? (
      <Check className="h-3.5 w-3.5 text-primary" />
    ) : state === "error" ? (
      <XCircle className="h-3.5 w-3.5 text-destructive" />
    ) : state === "running" ? (
      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
    ) : (
      <Circle className="h-3 w-3 text-muted-foreground/40" />
    );

  return (
    <li className={`flex items-center gap-2 ${tone}`}>
      {bullet}
      <span className={state === "running" ? "text-primary" : ""}>{icon}</span>
      {label}
    </li>
  );
}

export function ResumenAccion({
  usuario,
  mainType,
  accesoriosCount,
  flags,
  taskStates,
  onSubmit,
  isSubmitting,
  onSaveDraft,
  savingDraft,
}) {
  const tasks = [
    { key: "pdf", icon: <FileText className="h-3.5 w-3.5" />, label: "Generar PDF y Pagaré", show: true },
    { key: "email", icon: <Mail className="h-3.5 w-3.5" />, label: "Enviar correo al colaborador", show: flags.email },
    { key: "sync", icon: <RefreshCw className="h-3.5 w-3.5" />, label: "Sincronizar con YoSoySaludsa", show: flags.sync },
    { key: "sign", icon: <ShieldCheck className="h-3.5 w-3.5" />, label: "Marcar como firmada", show: flags.autoSign },
  ];

  return (
    <aside className="sticky top-6 rounded-2xl border border-border bg-card p-5 shadow-sm">
      <h3 className="text-base font-bold text-foreground">Resumen de Acción</h3>

      <dl className="mt-4 space-y-2.5 text-sm">
        <Row label="Colaborador" value={usuario.full_name || "No seleccionado"} muted={!usuario.full_name} />
        <Row label="Equipo" value={String(mainType)} />
        <Row label="Accesorios" value={`${accesoriosCount} items`} />
      </dl>

      <div className="mt-5 rounded-xl bg-muted/60 p-3">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          Tareas a ejecutar
        </p>
        <ul className="space-y-1.5 text-xs">
          {tasks
            .filter((t) => t.show)
            .map((t) => (
              <Task key={t.key} icon={t.icon} label={t.label} state={taskStates[t.key]} />
            ))}
        </ul>
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={isSubmitting}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground shadow transition hover:bg-primary/90 disabled:opacity-60"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" /> Generando...
          </>
        ) : (
          <>
            Generar Acta <ArrowRight className="h-4 w-4" />
          </>
        )}
      </button>

      {onSaveDraft && (
        <button
          type="button"
          onClick={onSaveDraft}
          disabled={savingDraft || isSubmitting}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-border bg-background px-4 py-3 text-sm font-semibold text-foreground shadow-sm transition hover:bg-muted disabled:opacity-60"
        >
          {savingDraft ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Guardando...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" /> Guardar Borrador
            </>
          )}
        </button>
      )}
    </aside>
  );
}
