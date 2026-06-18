import { useState } from "react";
import { Link } from "react-router-dom";
import { generateDiscount } from "@/lib/api";
import { 
  ArrowLeft, CheckCircle2, FileText, Download, DollarSign, 
  Laptop, Monitor, Plug, Mouse, Keyboard, Headphones, Briefcase, HelpCircle 
} from "lucide-react";
import { toast } from "sonner";
import '../styles/styles.css';
import { EMPTY_USER, ACCESORIO_DEFAULTS } from "@/lib/acta-defaults"; // 1. Importamos ACCESORIO_DEFAULTS
import { ColaboradorSearch } from "@/components/actas/ColaboradorSearch";
import { Modal } from "@/components/actas/Modal";

// 2. Agregamos Mochila y Otros con sus respectivos Iconos
const EQUIPMENT_OPTIONS = [
  { id: "Laptop", icon: Laptop, label: "Laptop" },
  { id: "Diadema", icon: Headphones, label: "Diadema" },
  { id: "Monitor", icon: Monitor, label: "Monitor" },
  { id: "Cargador", icon: Plug, label: "Cargador" },
  { id: "Teclado", icon: Keyboard, label: "Teclado" },
  { id: "Mouse", icon: Mouse, label: "Mouse" },
  { id: "Mochila", icon: Briefcase, label: "Mochila" },
  { id: "Otros", icon: HelpCircle, label: "Otros" },
];

function StepCard({ step, title, children }) {
  return (
    <section className="relative z-10 rounded-2xl border border-border bg-card p-6 shadow-sm">
      <header className="mb-5 flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
          {step}
        </span>
        <h2 className="text-lg font-bold text-foreground">{title}</h2>
      </header>
      {children}
    </section>
  );
}

export default function NuevoDescuento() {
  const [usuario, setUsuario] = useState(EMPTY_USER);
  const [deductionMonth, setDeductionMonth] = useState("");

  const [equipoType, setEquipoType] = useState(null);
  const [equipo, setEquipo] = useState({
    manufacturer: "",
    model: "",
    serial_number: "",
    purchase_cost: 0,
    quantity: 1
  });

  // Estado adicional para cuando se selecciona "Otros"
  const [otrosDescripcion, setOtrosDescripcion] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false);
  const [generatedFile, setGeneratedFile] = useState(null);

  // 3. Función clave para interceptar el cambio de equipo y auto-rellenar los datos
  const handleSelectEquipoType = (type) => {
    setEquipoType(type);

    // Buscamos si existen valores predeterminados para este tipo
    const defaults = ACCESORIO_DEFAULTS[type];

    if (defaults) {
      setEquipo({
        manufacturer: defaults.manufacturer || "",
        model: defaults.model || "",
        serial_number: "", // El SN siempre debe ingresarse manualmente por seguridad
        purchase_cost: defaults.purchase_cost || 0,
        quantity: 1
      });
    } else {
      // Fallback para Laptop o si no se encuentra en el diccionario de defaults
      setEquipo({
        manufacturer: type === "Laptop" ? "Lenovo" : "",
        model: "",
        serial_number: "",
        purchase_cost: 0,
        quantity: 1
      });
    }

    // Resetear descripción alternativa si cambian de opción
    if (type !== "Otros") {
      setOtrosDescripcion("");
    }
  };

  const handleEquipoChange = (field, value) => {
    setEquipo(prev => ({ ...prev, [field]: value }));
  };

  const buildPayload = () => {
    // Si es "Otros", enviamos la descripción personalizada como el tipo de equipo
    const finalEquipmentType = equipoType === "Otros" ? otrosDescripcion : equipoType;

    return {
      usuario: {
        username: usuario.username, // Enviamos el username requerido por el backend
        full_name: usuario.full_name,
        national_id: usuario.national_id || usuario.cedula || "NA"
      },
      deduction_month: deductionMonth,
      equipos: [
        {
          equipment_type: finalEquipmentType,
          manufacturer: equipo.manufacturer || "NA",
          model: equipo.model || "NA",
          serial_number: equipo.serial_number || "NA",
          purchase_cost: parseFloat(equipo.purchase_cost) || 0,
          quantity: 1
        }
      ]
    };
  };

  const validate = () => {
    if (!usuario.username && !usuario.full_name) return "Selecciona un colaborador.";
    if (!deductionMonth.trim()) return "El mes a descontar es obligatorio (Ej. Julio 2026).";
    if (!equipoType) return "Debes marcar el tipo de equipo a descontar.";
    if (equipoType === "Otros" && !otrosDescripcion.trim()) return "Por favor, especifique el tipo de equipo en la descripción.";
    if (!equipo.manufacturer.trim()) return "La marca del equipo es obligatoria.";
    if (equipo.purchase_cost <= 0) return "El monto a descontar debe ser mayor a 0.";
    return null;
  };

  const onClickGenerate = () => {
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }
    setConfirmOpen(true);
  };

  const handleConfirm = async () => {
    const payload = buildPayload();
    setConfirmOpen(false);
    setSubmitting(true);

    try {
      const result = await generateDiscount(payload);
      setGeneratedFile(result?.filename || `DESCUENTO_${usuario.username || 'EMPLEADO'}.pdf`);
      setSuccessOpen(true);
      toast.success("Acta de descuento generada correctamente");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error desconocido";
      toast.error("No se pudo generar el documento", { description: msg });
    } finally {
      setSubmitting(false);
    }
  };

  const resetAll = () => {
    setUsuario(EMPTY_USER);
    setDeductionMonth("");
    setEquipoType(null);
    setEquipo({ manufacturer: "", model: "", serial_number: "", purchase_cost: 0, quantity: 1 });
    setOtrosDescripcion("");
    setGeneratedFile(null);
    setSuccessOpen(false);
  };

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <ArrowLeft className="h-4 w-4" />
            </span>
            Actas de Descuento
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Generar Acta de Descuento</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Complete los datos para generar el documento legal de descuento. Solo se permite un equipo por acta.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">

            {/* PASO 1: Empleado y Mes */}
            <StepCard step={1} title="Datos del Colaborador">
              <ColaboradorSearch usuario={usuario} onChange={setUsuario} />

              <div className="mt-6 border-t border-border pt-6">
                <label className="mb-2 block text-sm font-semibold text-foreground">Mes de Aplicación del Descuento</label>
                <input
                  type="text"
                  placeholder="Ej. Octubre 2026"
                  value={deductionMonth}
                  onChange={(e) => setDeductionMonth(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>
            </StepCard>

            {/* PASO 2: Selección Única de Equipo */}
            <StepCard step={2} title="Equipo a Descontar">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {EQUIPMENT_OPTIONS.map((opt) => {
                  const Icon = opt.icon;
                  const isSelected = equipoType === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => handleSelectEquipoType(opt.id)}
                      className={`flex flex-col items-center justify-center gap-2 rounded-xl border p-4 transition-all ${
                        isSelected
                          ? "border-primary bg-primary/5 text-primary shadow-sm ring-1 ring-primary"
                          : "border-border bg-card text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                      }`}
                    >
                      <Icon className="h-6 w-6" />
                      <span className="text-sm font-medium">{opt.label}</span>
                    </button>
                  );
                })}
              </div>

              {equipoType && (
                <div className="mt-6 animate-in fade-in slide-in-from-top-4 space-y-4 rounded-xl border border-border bg-muted/20 p-5">
                  
                  {/* INPUT CONDICIONAL PARA OTROS */}
                  {equipoType === "Otros" && (
                    <div className="animate-in zoom-in-95">
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">Descripción del Equipo *</label>
                      <input
                        type="text"
                        value={otrosDescripcion}
                        onChange={(e) => setOtrosDescripcion(e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:ring-1 focus:ring-primary"
                        placeholder="Ej. Silla Ergonómica, Regulador de Voltaje"
                      />
                    </div>
                  )}

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">Marca *</label>
                      <input
                        type="text"
                        value={equipo.manufacturer}
                        onChange={(e) => handleEquipoChange("manufacturer", e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                        placeholder="Ej. Dell, Apple"
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">Modelo</label>
                      <input
                        type="text"
                        value={equipo.model}
                        onChange={(e) => handleEquipoChange("model", e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm"
                        placeholder="Ej. Latitude 5420"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className="mb-1 block text-xs font-medium text-muted-foreground">Número de Serie (SN)</label>
                      <input
                        type="text"
                        value={equipo.serial_number}
                        onChange={(e) => handleEquipoChange("serial_number", e.target.value)}
                        className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm font-mono uppercase"
                        placeholder="Ej. ABC123XYZ"
                      />
                    </div>
                  </div>

                  {/* MONTO A DESCONTAR */}
                  <div className="mt-4 rounded-lg bg-primary/10 p-4 border border-primary/20">
                    <label className="mb-2 flex items-center gap-2 text-sm font-bold text-primary">
                      <DollarSign className="h-4 w-4" />
                      Monto a Descontar *
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={equipo.purchase_cost || ""}
                        onChange={(e) => handleEquipoChange("purchase_cost", e.target.value)}
                        className="w-full rounded-md border border-input bg-background py-2 pl-7 pr-3 text-lg font-bold text-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="0.00"
                      />
                    </div>
                    <p className="mt-1.5 text-xs text-primary/80">Este valor se convertirá a letras automáticamente en el acta.</p>
                  </div>
                </div>
              )}
            </StepCard>
          </div>

          {/* SIDEBAR */}
          <div className="sticky top-20 self-start rounded-2xl border border-border bg-card p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-muted-foreground">
              Resumen de Generación
            </h3>
            <ul className="mb-6 space-y-3 text-sm">
              <li className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">Colaborador:</span>
                <span className="font-semibold text-foreground text-right">
                  {usuario.full_name || "No seleccionado"}
                </span>
              </li>
              <li className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">Mes:</span>
                <span className="font-semibold text-foreground">
                  {deductionMonth || "—"}
                </span>
              </li>
              <li className="flex justify-between border-b border-border pb-2">
                <span className="text-muted-foreground">Equipo:</span>
                <span className="font-semibold text-foreground">
                  {equipoType === "Otros" && otrosDescripcion ? otrosDescripcion : (equipoType || "Ninguno")}
                </span>
              </li>
              <li className="flex justify-between pt-2">
                <span className="font-bold text-foreground">Total a descontar:</span>
                <span className="text-lg font-black text-primary">
                  ${parseFloat(equipo.purchase_cost || 0).toFixed(2)}
                </span>
              </li>
            </ul>

            <button
              onClick={onClickGenerate}
              disabled={submitting}
              className="w-full rounded-full bg-primary px-4 py-3 text-sm font-bold text-primary-foreground transition-all hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? "Generando documento..." : "Generar Acta de Descuento"}
            </button>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              Solo se generará el archivo DOCX/PDF. No se enviarán correos automáticos.
            </p>
          </div>
        </div>
      </main>

      {/* MODAL CONFIRMACIÓN */}
      <Modal open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Confirmar Generación" size="md" footer={
        <>
          <button type="button" onClick={() => setConfirmOpen(false)} className="rounded-full bg-muted px-4 py-1.5 text-sm font-semibold text-foreground hover:bg-muted/70">Cancelar</button>
          <button type="button" onClick={handleConfirm} className="rounded-full bg-primary px-4 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90">Confirmar Descuento</button>
        </>
      }>
        <p className="text-sm text-muted-foreground">Estás por generar un acta de descuento para:</p>
        <div className="mt-4 rounded-lg border border-border bg-muted/30 p-4">
          <p className="font-bold">{usuario.full_name}</p>
          <p className="text-sm text-muted-foreground">Mes de descuento: {deductionMonth}</p>
          <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
            <span className="text-sm">
              {equipoType === "Otros" ? otrosDescripcion : equipoType} ({equipo.manufacturer})
            </span>
            <span className="font-bold text-destructive">-${parseFloat(equipo.purchase_cost).toFixed(2)}</span>
          </div>
        </div>
      </Modal>

      {/* MODAL ÉXITO */}
      <Modal open={successOpen} onClose={() => setSuccessOpen(false)} title="Acta Generada" size="md" footer={
        <>
          <button type="button" onClick={() => setSuccessOpen(false)} className="rounded-full bg-muted px-4 py-1.5 text-sm font-semibold text-foreground hover:bg-muted/70">Cerrar</button>
          <button type="button" onClick={resetAll} className="rounded-full bg-primary px-4 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90">Nueva Acta</button>
        </>
      }>
        <div className="flex items-start gap-3 mb-5">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
            <CheckCircle2 className="h-6 w-6" />
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">El acta de descuento está lista.</p>
            <p className="text-xs text-muted-foreground">El archivo debería descargarse automáticamente en tu navegador.</p>
          </div>
        </div>
        {generatedFile && (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2 text-sm">
            <span className="flex min-w-0 items-center gap-2">
              <FileText className="h-4 w-4 shrink-0 text-primary" />
              <span className="truncate font-medium text-foreground">{generatedFile}</span>
            </span>
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Download className="h-3 w-3" />
            </span>
          </div>
        )}
      </Modal>
    </div>
  );
}