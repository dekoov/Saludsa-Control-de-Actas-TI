import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  ClipboardList,
  CalendarClock,
  FileText,
  BadgeCheck,
  FilePen,
  PenLine,
  CloudUpload,
  User,
  MapPin,
} from "lucide-react";
import { getDashboardStats, getRecentUsers } from "@/lib/api";
import Layout from "@/components/shared/Layout";
import HelpCard from "@/components/shared/HelpCard";

const STATS_CONFIG = [
  {
    label: "Actas Totales",
    key: "total_actas",
    icon: ClipboardList,
    tone: "bg-primary/10 text-primary",
  },
  {
    label: "Pendientes Firma",
    key: "pendientes_firma",
    icon: CalendarClock,
    tone: "bg-destructive/10 text-destructive",
  },
  {
    label: "Borradores",
    key: "borradores",
    icon: FileText,
    tone: "bg-muted text-muted-foreground",
  },
  {
    label: "Pendientes en YoSoySaludsa",
    key: "pendientes_saludsa",
    icon: BadgeCheck,
    tone: "bg-primary/10 text-primary",
  },
];

const ATTENTION = [
  {
    title: "Actas guardadas en borrador",
    description: "Tienes actas incompletas que requieren tu revisión para ser procesadas.",
    icon: FilePen,
    accent: "before:bg-primary",
    iconTone: "bg-primary/10 text-primary",
    path: "/historial?tab=borradores"
  },
  {
    title: "Acta pendiente de firma",
    description: "Existen documentos listos que requieren la firma electrónica del responsable.",
    icon: PenLine,
    accent: "before:bg-destructive",
    iconTone: "bg-destructive/10 text-destructive",
    path: "/historial?estado=PENDIENTE_FIRMA"
  },
  {
    title: "Acta pendiente de registro en YoSoySaludsa",
    description: "Sincronización pendiente con el sistema central de recursos humanos.",
    icon: CloudUpload,
    accent: "before:bg-primary",
    iconTone: "bg-primary/10 text-primary",
    path: "/historial?solo_atencion=true"
  },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentUsers, setRecentUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDashboardStats(), getRecentUsers()])
      .then(([s, u]) => {
        setStats(s);
        setRecentUsers(u);
      })
      .catch((err) => {
        console.error("Error fetching dashboard data:", err);
      })
      .finally(() => setLoading(false));
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "—";
    const date = new Date(dateString);
    return date.toLocaleDateString("es-EC", { day: "2-digit", month: "2-digit", year: "numeric" });
  };

  const getStatValue = (key) => {
    if (loading) return "Cargando...";
    if (!stats) return "—";
    return stats[key] ?? "—";
  };

  return (
    <Layout title="Dashboard">
      {/* Resumen */}
      <section className="mb-8">
        <h2 className="text-lg font-bold text-foreground">Resumen</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Estado actual de la gestión de activos y actas.
        </p>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {STATS_CONFIG.map(({ label, key, icon: Icon, tone }) => (
            <div key={label} className="rounded-2xl bg-background p-5 shadow-sm">
              <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone}`}>
                <Icon className="h-5 w-5" />
              </div>
              <p className="mt-4 text-3xl font-extrabold tracking-tight text-foreground">
                {getStatValue(key)}
              </p>
              <p className="mt-1 text-[11px] font-bold uppercase tracking-wider text-primary">
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Atención + Usuarios */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <h2 className="mb-4 text-lg font-bold text-foreground">Atención Requerida</h2>
          <div className="space-y-3">
            {ATTENTION.map(({ title, description, icon: Icon, accent, iconTone, path }) => (
              <article
                key={title}
                className={`relative overflow-hidden rounded-2xl bg-background p-5 pl-6 shadow-sm before:absolute before:left-0 before:top-0 before:h-full before:w-1.5 ${accent}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${iconTone}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-bold text-foreground sm:text-base">{title}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{description}</p>
                  </div>
                  <button
                    onClick={() => navigate(path)}
                    className="shrink-0 rounded-lg bg-muted px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-muted/70 sm:inline-flex"
                  >
                    Gestionar
                  </button>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-4 text-lg font-bold text-foreground">Últimos Usuarios</h2>
          <div className="rounded-2xl bg-background p-5 shadow-sm">
            <ul className="space-y-5">
              {recentUsers.length > 0 ? (
                recentUsers.map((u) => (
                  <li key={u.username}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-foreground">{u.full_name}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          Última acta: {formatDate(u.fecha_ultima_acta)}
                        </p>
                      </div>
                      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
                        Activo
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {u.username}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {u.city}
                      </span>
                    </div>
                  </li>
                ))
              ) : (
                <li className="text-sm text-muted-foreground">
                  {loading ? "Cargando usuarios..." : "No hay usuarios recientes"}
                </li>
              )}
            </ul>
          </div>

          {/* Componente Modularizado */}
          <HelpCard />
        </div>
      </section>
    </Layout>
  );
}
