import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { User, Lock, Eye, EyeOff, AlertCircle } from "lucide-react";
import saludsaLogo from "@/assets/saludsa-logo.png";
import { useAuth } from "@/context/AuthContext";

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;

    setLoading(true);
    setError("");

    try {
      const result = await login(username, password);

      if (result.success) {
        navigate("/");
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError("No se pudo conectar con el servidor local de Saludsa.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-md rounded-3xl bg-background p-8 shadow-xl sm:p-10">
          {/* Logo */}
          <div className="flex justify-center">
            <img src={saludsaLogo} alt="Saludsa" className="h-12 w-auto" />
          </div>

          {/* Title */}
          <div className="mt-6 text-center">
            <h1 className="text-xl font-extrabold tracking-tight text-foreground sm:text-2xl">
              Bienvenido al Gestor de Actas
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Ingresa con tus credenciales de Active Directory
            </p>
          </div>

          {/* CONTENEDOR DE ERROR */}
          {error && (
            <div className="mt-5 flex items-center gap-2 rounded-2xl bg-red-50 p-4 text-xs font-semibold text-red-600 ring-1 ring-red-200">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
                Usuario
              </label>
              <div className="relative">
                <User className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={username}
                  disabled={loading}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Ej: lzambrano"
                  autoComplete="username"
                  className="w-full rounded-full bg-muted/60 py-3 pl-11 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-60"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type={showPwd ? "text" : "password"}
                  value={password}
                  disabled={loading}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  autoComplete="current-password"
                  className="w-full rounded-full bg-muted/60 py-3 pl-11 pr-11 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-60"
                />
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => setShowPwd((s) => !s)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground transition hover:text-foreground disabled:opacity-50"
                  aria-label={showPwd ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="text-right">
              <a
                href="https://passwordreset.microsoftonline.com/"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-bold text-primary hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-gradient-to-b from-primary to-primary/80 py-3.5 text-sm font-bold text-primary-foreground shadow-lg shadow-primary/30 transition hover:from-primary/95 hover:to-primary disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  Verificando credenciales…
                </>
              ) : (
                "Iniciar Sesión"
              )}
            </button>
          </form>
        </div>
      </main>

      <footer className="px-4 pb-6 text-center">
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
          © 2026 Saludsa Control de Actas TI
        </p>
        <div className="mt-2 flex items-center justify-center gap-3 text-[10px] font-bold uppercase tracking-[0.2em]">
          <a href="https://www.linkedin.com/in/david-correa-beltran/" className="text-muted-foreground hover:text-foreground">
            Desarrollado por: David Correa
          </a>
          <span className="text-muted-foreground">•</span>
          <a href="https://saludsa-help.saludsa.com.ec/self-service" className="text-muted-foreground hover:text-foreground">
            Soporte IT
          </a>
        </div>
      </footer>
    </div>
  );
}

export default LoginPage;
