import { useState } from "react";

export function Tooltip({ content, children, side = "top" }) {
  const [open, setOpen] = useState(false);
  const pos = side === "top" ? "bottom-full mb-2" : "top-full mt-2";
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {open && (
        <span
          role="tooltip"
          className={`pointer-events-none absolute left-1/2 z-50 ${pos} -translate-x-1/2 whitespace-nowrap rounded-md bg-foreground px-2.5 py-1 text-[11px] font-medium text-background shadow-lg`}
        >
          {content}
        </span>
      )}
    </span>
  );
}
