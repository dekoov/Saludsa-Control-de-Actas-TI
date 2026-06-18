import { Link } from "react-router-dom";
import {
  FilePlus2,
  FileText,
  Settings,
  LogOut,
  User,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Sidebar({ className }) {
  const { user, logout } = useAuth();

  return (
    <aside className={`flex shrink-0 flex-col bg-background px-5 py-6 ${className}`}>
      <Link to="/" className="mb-10 block cursor-pointer hover:opacity-90 transition-opacity">
        <div className="text-2xl font-extrabold tracking-tight text-primary">
          Salud
          <span className="text-foreground">sa</span>
        </div>
        <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
          <span>Control de Actas TI</span>
        </p>
      </Link>

      <nav className="flex flex-col gap-1">
        <Link
          to="/nueva-acta"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
        >
          <FilePlus2 className="h-4 w-4" />
          Nueva Acta
        </Link>

        <Link
          to="/nuevo-descuento"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
        >
          <FilePlus2 className="h-4 w-4" />
          Nuevo Descuento
        </Link>


        <Link
          to="/historial"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
        >
          <FileText className="h-4 w-4" />
          Historial
        </Link>

        <p className="mt-6 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
          Administración
        </p>
        <a
          href="https://github.com/dekoov/Saludsa-Control-de-Actas-TI"
          className="mt-2 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
        >
          <Settings className="h-4 w-4" />
          Repositorio
        </a>
      </nav>

      <div className="mt-auto flex items-center gap-3 border-t border-border pt-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
          <User className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-foreground">
            {user?.full_name || "Usuario"}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {user?.position || "Usuario"}
          </p>
        </div>
        <button
          onClick={logout}
          className="text-muted-foreground transition hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </aside>
  );

}
