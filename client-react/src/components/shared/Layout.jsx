import { Link } from "react-router-dom";
import Sidebar from "@/components/shared/Sidebar";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import {
  Menu,
  Plus,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function Layout({ children, title = "Dashboard" }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-muted/30 animate-fade-in">
      {/* Sidebar */}
      <Sidebar className="hidden w-64 lg:flex" />

      {/* Main Container */}
      <main className="flex-1 px-5 py-6 sm:px-8">
        {/* Topbar */}
        <header className="mb-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <button className="rounded-lg p-2 text-muted-foreground transition hover:bg-muted lg:hidden">
                  <Menu className="h-5 w-5" />
                </button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <SheetTitle className="sr-only">Menú de Navegación móvil</SheetTitle>
                <SheetDescription className="sr-only">Accede a las opciones de la aplicación</SheetDescription>
                <div className="flex flex-col h-full px-5 py-6">
                  <Sidebar className="h-full w-full" />
                </div>
              </SheetContent>
            </Sheet>
            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              {title}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/nueva-acta"
              className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              Nueva Acta
            </Link>
          </div>
        </header>

        {/* Contenido dinámico de la página */}
        {children}
      </main>
    </div>
  );
}
