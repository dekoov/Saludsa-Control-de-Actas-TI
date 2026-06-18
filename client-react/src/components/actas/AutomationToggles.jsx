import { Mail, RefreshCw, ShieldCheck } from "lucide-react";

function ToggleRow({ icon, title, description, checked, onChange, badge, children }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-1 items-start gap-3">
          <span className="mt-0.5 text-primary">{icon}</span>
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-foreground">{title}</h4>
              {badge}
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
            {checked && children}
          </div>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          onClick={() => onChange(!checked)}
          className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition ${checked ? "bg-primary" : "bg-muted"
            }`}
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-background shadow transition ${checked ? "translate-x-5" : "translate-x-0.5"
              }`}
          />
        </button>
      </div>
    </div>
  );
}

export function AutomationToggles({
  sendEmail,
  setSendEmail,
  emailType,
  setEmailType,
  syncHrPortal,
  setSyncHrPortal,
  autoSign,
  setAutoSign,
}) {
  return (
    <div className="space-y-3">
      <ToggleRow
        icon={<Mail className="h-5 w-5" />}
        title="Enviar correo automático al colaborador"
        description="Notifica al usuario sobre la nueva acta con el PDF adjunto."
        checked={sendEmail}
        onChange={setSendEmail}
      >
        <div className="mt-3 flex flex-wrap gap-4 text-sm">
          {["Dotacion", "Renovacion"].map((t) => (
            <label key={t} className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="emailType"
                checked={emailType === t}
                onChange={() => setEmailType(t)}
                className="h-4 w-4 accent-primary"
              />
              <span className="text-foreground">{t}</span>
            </label>
          ))}
        </div>
      </ToggleRow>

      <ToggleRow
        icon={<RefreshCw className="h-5 w-5" />}
        title="Sincronizar con YoSoySaludsa"
        description="Registra el equipo en el perfil del usuario."
        checked={syncHrPortal}
        onChange={setSyncHrPortal}
      />

      <ToggleRow
        icon={<ShieldCheck className="h-5 w-5" />}
        title="Marcar automáticamente como firmada"
        description="Omite el proceso de firma digital para este registro específico."
        checked={autoSign}
        onChange={setAutoSign}
      />
    </div>
  );
}
