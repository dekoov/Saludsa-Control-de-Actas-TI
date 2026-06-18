import { useEffect, useRef, useState } from "react";
import { Search, User as UserIcon, MapPin, IdCard, Loader2 } from "lucide-react";
import { searchADUsers, adUserToUsuario } from "@/lib/api";

export function ColaboradorSearch({ usuario, onChange }) {
  const [query, setQuery] = useState(usuario.full_name);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      const data = await searchADUsers(query);
      setResults(data);
      setLoading(false);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  const selected = !!usuario.username;

  return (
    <div className="relative">
      <label className="mb-2 block text-sm font-semibold text-foreground">
        Buscar Colaborador
      </label>
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            if (!e.target.value)
              onChange({ username: "", full_name: "", national_id: "", city: "" });
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Buscar en Active Directory (Nombre, Usuario...)"
          className="h-12 w-full rounded-lg border border-input bg-muted/60 py-2.5 pl-10 pr-10 text-sm outline-none ring-primary/30 transition focus:border-primary focus:ring-2"
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-primary" />
        )}
      </div>

      {open && (results.length > 0 || (query.length >= 2 && !loading)) && (
        <div className="absolute left-0 right-0 top-full z-[9999] mt-2 max-h-80 overflow-auto rounded-xl border border-border bg-card shadow-2xl">
          {results.length === 0 ? (
            <div className="px-4 py-6 text-center text-sm text-muted-foreground">
              Sin resultados para "{query}"
            </div>
          ) : (
            results.map((u) => (
              <button
                key={u.username}
                type="button"
                onMouseDown={() => {
                  const usr = adUserToUsuario(u);
                  onChange(usr);
                  setQuery(usr.full_name);
                  setOpen(false);
                }}
                className="group flex w-full items-start gap-3 border-b border-border/40 px-4 py-3 text-left transition last:border-0 hover:bg-primary/5"
              >
                <span className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <UserIcon className="h-4 w-4" />
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-bold text-foreground group-hover:text-primary">
                      {u.full_name}
                    </p>
                    <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
                      Activo
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {u.username}
                    {u.position ? ` · ${u.position}` : ""}
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {u.city}
                    </span>
                    <span className="flex items-center gap-1">
                      <IdCard className="h-3 w-3" /> {u.national_id}
                    </span>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {selected && (
        <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-primary/30 bg-primary/5 p-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground">
              <UserIcon className="h-4 w-4" />
            </span>
            <div>
              <p className="text-sm font-bold text-foreground">{usuario.full_name}</p>
              <p className="text-xs text-muted-foreground">
                {usuario.username} · CI {usuario.national_id} · {usuario.city}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              onChange({ username: "", full_name: "", national_id: "", city: "" });
              setQuery("");
            }}
            className="rounded-full px-3 py-1 text-xs font-semibold text-primary hover:bg-primary/10"
          >
            Cambiar
          </button>
        </div>
      )}
    </div>
  );
}
