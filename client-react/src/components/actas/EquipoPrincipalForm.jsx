import { Laptop, Monitor } from "lucide-react";
import { Field } from "@/components/shared/Field";
import { AutocompleteField } from "@/components/shared/AutocompleteField";

const INITIAL_MODELS = ["V14 G3 IAP", "V14 G4 AMN", "Thinkpad L14 Gen", "IdeaPad 3 14ITL6"];
const INITIAL_COSTS = ["400", "1200"];

const inputCls =
  "w-full rounded-lg border border-input bg-muted px-3 py-2.5 text-sm outline-none ring-primary/30 transition focus:border-primary focus:ring-2";

export function EquipoPrincipalForm({ equipo, onChange }) {
  const update = (key, value) => onChange({ ...equipo, [key]: value });
  const isLaptop = equipo.equipment_type === "Laptop";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3">
        {[
          { type: "Laptop", icon: Laptop },
          { type: "Desktop", icon: Monitor },
        ].map(({ type, icon: Icon }) => {
          const active = equipo.equipment_type === type;
          return (
            <button
              key={type}
              type="button"
              onClick={() => update("equipment_type", type)}
              className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 py-6 transition ${active ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40"
                }`}
            >
              <Icon className={`h-7 w-7 ${active ? "text-primary" : "text-muted-foreground"}`} />
              <span className={`text-sm font-medium ${active ? "text-primary" : "text-foreground"}`}>
                {type}
              </span>
            </button>
          );
        })}
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <h4 className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <span className="h-4 w-1 rounded-full bg-primary" /> Datos Obligatorios
          </h4>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Hostname" required={isLaptop}>
            <input
              type="text"
              value={equipo.hostname ?? ""}
              onChange={(e) => update("hostname", e.target.value)}
              placeholder="Ej. LPT-UIO-0123"
              className={inputCls}
            />
          </Field>

          <Field label="Marca" required>
            <input
              type="text"
              value={equipo.manufacturer ?? ""}
              onChange={(e) => update("manufacturer", e.target.value)}
              placeholder="Ej. Dell, Lenovo, Apple"
              className={inputCls}
            />
          </Field>

          <AutocompleteField
            label="Modelo"
            value={equipo.model}
            onChange={(val) => update("model", val)}
            storageKey="saludsa_custom_models"
            initialOptions={INITIAL_MODELS}
            placeholder="Ej. Latitude 5420"
          />

          <Field label="Serial" required={isLaptop}>
            <input
              type="text"
              value={equipo.serial_number ?? ""}
              onChange={(e) => update("serial_number", e.target.value)}
              placeholder="Número de serie"
              className={inputCls}
            />
          </Field>

          {/* AQUÍ ESTÁ LA SOLUCIÓN DEL BACKEND: type="number" y Number(val) */}
          <AutocompleteField
            label="Valor"
            type="number"
            value={equipo.purchase_cost === 0 ? "" : equipo.purchase_cost}
            onChange={(val) => update("purchase_cost", val === "" ? 0 : Number(val))}
            storageKey="saludsa_custom_costs"
            initialOptions={INITIAL_COSTS}
            placeholder="0.00"
            prefix="$"
          />

          <Field label="Cantidad" required>
            <input
              type="number"
              min="1"
              value={equipo.quantity || 1}
              onChange={(e) => update("quantity", parseInt(e.target.value) || 1)}
              placeholder="1"
              className={inputCls}
            />
          </Field>

          <Field label="Estado Físico" required>
            <div className="flex h-[42px] items-center gap-5">
              {["Nuevo", "Usado"].map((s) => (
                <label key={s} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="status"
                    checked={equipo.status === s}
                    onChange={() => update("status", s)}
                    className="h-4 w-4 accent-primary"
                  />
                  <span className="text-foreground">{s}</span>
                </label>
              ))}
            </div>
          </Field>
        </div>
      </section>

      <section>
        <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-foreground">
          <span className="h-4 w-1 rounded-full bg-primary" /> Datos Adicionales
        </h4>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Procesador">
            <input
              type="text"
              placeholder="Ej. Intel Core i7 12th Gen"
              className={inputCls}
              value={equipo.observation?.split("|proc:")[1]?.split("|")[0] ?? ""}
              onChange={(e) => {
                const base = (equipo.observation || "").replace(/\|proc:[^|]*/g, "");
                update("observation", `${base}|proc:${e.target.value}`);
              }}
            />
          </Field>
          <Field label="Sistema Operativo">
            <select
              className={inputCls}
              defaultValue="Windows 11 Pro"
              onChange={(e) => {
                const base = (equipo.observation || "").replace(/\|os:[^|]*/g, "");
                update("observation", `${base}|os:${e.target.value}`);
              }}
            >
              <option>Windows 11 Pro</option>
              <option>Windows 10 Pro</option>
              <option>macOS</option>
              <option>Linux</option>
            </select>
          </Field>
          <Field label="Año de Compra">
            <input type="number" placeholder="YYYY" min="2000" max="2099" className={inputCls} />
          </Field>
        </div>
        <div className="mt-4">
          <Field label="Observaciones">
            <textarea
              placeholder="Observaciones adicionales sobre el equipo..."
              className={`${inputCls} min-h-[80px] resize-y`}
              value={equipo.observation ?? ""}
              onChange={(e) => update("observation", e.target.value)}
            />
          </Field>
        </div>
      </section>
    </div>
  );
}
