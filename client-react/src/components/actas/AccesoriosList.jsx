import { Headphones, Plug, Backpack, Package, ChevronDown, Monitor, Keyboard, Mouse } from "lucide-react";
import { ACCESORIO_TYPES } from "@/lib/acta-defaults";

const META = {
  Diadema: { label: "Diadema", icon: Headphones },
  Cargador: { label: "Cargador", icon: Plug },
  Mochila: { label: "Mochila", icon: Backpack },
  Monitor: { label: "Monitor", icon: Monitor },
  Teclado: { label: "Teclado", icon: Keyboard },
  Mouse: { label: "Mouse", icon: Mouse },
  Otros: { label: "Otros", icon: Package },
};

const fieldCls =
  "h-10 w-full rounded-lg border border-input bg-muted/60 px-3 text-sm outline-none ring-primary/30 transition focus:border-primary focus:ring-2";

function Field({ label, children }) {
  return (
    <div>
      <label className="mb-1 ml-1 block text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </label>
      {children}
    </div>
  );
}

export function AccesoriosList({ items = [], onToggle, onUpdate }) {
  return (
    <div className="space-y-3">
      {ACCESORIO_TYPES.map((type) => {
        const { label, icon: Icon } = META[type];
        const active = items.find((i) => i.type === type);
        return (
          <div
            key={type}
            className={`overflow-hidden rounded-xl border transition ${active ? "border-primary/40 bg-primary/5" : "border-border bg-card"
              }`}
          >
            <label className="flex cursor-pointer items-center gap-3 p-4 hover:bg-primary/5">
              <input
                type="checkbox"
                checked={!!active}
                onChange={() => onToggle(type)}
                className="h-5 w-5 rounded accent-primary"
              />
              <Icon className={`h-5 w-5 ${active ? "text-primary" : "text-muted-foreground"}`} />
              <span className="flex-1 text-sm font-bold text-foreground">{label}</span>
              {active && <ChevronDown className="h-4 w-4 text-primary" />}
            </label>

            {active && (
              <div className="grid grid-cols-1 gap-3 border-t border-border/60 bg-background/60 p-4 sm:grid-cols-2 lg:grid-cols-3">
                <Field label="Cantidad">
                  <input
                    type="number"
                    min="1"
                    className={fieldCls}
                    value={active.quantity || 1}
                    onChange={(e) => onUpdate(type, { quantity: parseInt(e.target.value) || 1 })}
                    placeholder="1"
                  />
                </Field>
                <Field label="Marca">
                  <input
                    className={fieldCls}
                    value={active.manufacturer}
                    onChange={(e) => onUpdate(type, { manufacturer: e.target.value })}
                    placeholder="Ej. Poly"
                  />
                </Field>
                <Field label="Modelo">
                  <input
                    className={fieldCls}
                    value={active.model}
                    onChange={(e) => onUpdate(type, { model: e.target.value })}
                    placeholder="Modelo"
                  />
                </Field>
                <Field label="Serie">
                  <input
                    className={fieldCls}
                    value={active.serial_number}
                    onChange={(e) => onUpdate(type, { serial_number: e.target.value })}
                    placeholder="S/N (opcional)"
                  />
                </Field>
                <Field label="Valor">
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                      $
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      className={`${fieldCls} pl-6`}
                      value={active.purchase_cost || ""}
                      onChange={(e) =>
                        onUpdate(type, { purchase_cost: parseFloat(e.target.value) || 0 })
                      }
                    />
                  </div>
                </Field>
                <Field label="Estado">
                  <select
                    className={fieldCls}
                    value={active.status}
                    onChange={(e) => onUpdate(type, { status: e.target.value })}
                  >
                    <option>Nuevo</option>
                    <option>Usado</option>
                  </select>
                </Field>
                <Field label="Observaciones">
                  <input
                    className={fieldCls}
                    value={active.observation}
                    onChange={(e) => onUpdate(type, { observation: e.target.value })}
                    placeholder="..."
                  />
                </Field>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
