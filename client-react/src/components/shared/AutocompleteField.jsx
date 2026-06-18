import { useState, useRef, useEffect } from "react";
import { Field } from "./Field";

const inputCls =
  "w-full rounded-lg border border-input bg-muted px-3 py-2.5 text-sm outline-none ring-primary/30 transition focus:border-primary focus:ring-2";

export function AutocompleteField({
  label,
  value,
  onChange,
  storageKey,
  initialOptions = [],
  type = "text",
  prefix = "",
  ...props
}) {
  const [options, setOptions] = useState(() => {
    const saved = localStorage.getItem(storageKey);
    const parsed = saved ? JSON.parse(saved) : [];
    return Array.from(new Set([...initialOptions, ...parsed]));
  });

  const [show, setShow] = useState(false);
  const [index, setIndex] = useState(-1);
  const containerRef = useRef(null);

  // Filtrado
  const filtered = options.filter((o) =>
    String(o).toLowerCase().includes(String(value ?? "").toLowerCase())
  );

  // Guardado automático al escribir
  useEffect(() => {
    if (value && String(value).trim().length > 2) {
      const limpio = String(value).trim();
      const exists = options.some((o) => String(o).toLowerCase() === limpio.toLowerCase());

      if (!exists) {
        const timer = setTimeout(() => {
          const newOpts = [...options, limpio];
          setOptions(newOpts);
          localStorage.setItem(storageKey, JSON.stringify(newOpts.filter((o) => !initialOptions.includes(o))));
        }, 1500);
        return () => clearTimeout(timer);
      }
    }
  }, [value, options, initialOptions, storageKey]);

  // Manejo de teclado
  const handleKeyDown = (e) => {
    if (!show || filtered.length === 0) {
      if (e.key === "ArrowDown") setShow(true);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setIndex((prev) => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (index >= 0 && index < filtered.length) {
        onChange(filtered[index]);
        setShow(false);
        setIndex(-1);
      }
    } else if (e.key === "Escape") {
      setShow(false);
      setIndex(-1);
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <Field label={label} required={props.required}>
        <div className="relative">
          {prefix && (
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
              {prefix}
            </span>
          )}
          <input
            {...props}
            type={type}
            autoComplete="off"
            value={value ?? ""}
            onChange={(e) => {
              onChange(e.target.value);
              setShow(true);
              setIndex(-1);
            }}
            onFocus={() => setShow(true)}
            onBlur={() => setTimeout(() => setShow(false), 150)}
            onKeyDown={handleKeyDown}
            className={`${inputCls} ${prefix ? "pl-7" : ""}`}
          />
        </div>
      </Field>

      {show && filtered.length > 0 && (
        <ul className="absolute left-0 right-0 z-50 mt-1 max-h-48 overflow-y-auto rounded-lg border border-border bg-popover py-1 shadow-lg backdrop-blur-sm">
          {filtered.map((opt, i) => {
            const isSelected = i === index;
            return (
              <li key={opt}>
                <button
                  type="button"
                  // AQUÍ ESTÁ LA MAGIA: Cambiamos onClick por onMouseDown
                  onMouseDown={(e) => {
                    e.preventDefault(); // Evita que el input pierda el foco instantáneamente
                    onChange(opt);
                    setShow(false);
                    setIndex(-1);
                  }}
                  className={`w-full px-3 py-2 text-left text-sm transition-colors ${isSelected
                      ? "bg-primary font-medium text-primary-foreground"
                      : "text-popover-foreground hover:bg-accent hover:text-accent-foreground"
                    }`}
                >
                  {opt}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
