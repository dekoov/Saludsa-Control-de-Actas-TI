import { useMemo, useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { generateActa, saveDraft, getDraft, updateDraft } from "@/lib/api";
import { ArrowLeft, Info, CheckCircle2, FileText, Download, Save } from "lucide-react";
import { toast } from "sonner";
import '../styles/styles.css'
import {
  EMPTY_USER,
  emptyMainEquipo,
  ACCESORIO_DEFAULTS,
} from "@/lib/acta-defaults";
import { ColaboradorSearch } from "@/components/actas/ColaboradorSearch";
import { AutomationToggles } from "@/components/actas/AutomationToggles";
import { EquipoPrincipalForm } from "@/components/actas/EquipoPrincipalForm";
import { AccesoriosList } from "@/components/actas/AccesoriosList";
import { ResumenAccion } from "@/components/actas/ResumenAccion";
import { Modal } from "@/components/actas/Modal";
import { Tooltip } from "@/components/actas/Tooltip";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function StepCard({ step, title, right, children }) {
  return (
    <section className="relative z-10 rounded-2xl border border-border bg-card p-6 shadow-sm">
      <header className="mb-5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
            {step}
          </span>
          <h2 className="text-lg font-bold text-foreground">{title}</h2>
        </div>
        {right}
      </header>
      {children}
    </section>
  );
}

export default function NuevaActaPage() {
  const location = useLocation();
  const [usuario, setUsuario] = useState(EMPTY_USER);
  const [mainEquipo, setMainEquipo] = useState(emptyMainEquipo());
  const [includeMain, setIncludeMain] = useState(true);
  const [accesorios, setAccesorios] = useState([]);

  // Load draft data if coming from Historial
  useEffect(() => {
    const draftFromState = location.state?.draft;
    const queryParams = new URLSearchParams(location.search);
    const draftIdFromUrl = queryParams.get('draftId');

    const procesarYAsignarBorrador = (draftData) => {
      if (!draftData) return;

      setDraftId(draftData.id || draftData.draft_id || null);
      setUsuario(draftData.usuario || EMPTY_USER);

      // Recuperar estados de automatización de forma segura
      setAutoSign(draftData.marcar_firmada || false);
      setSyncHrPortal(draftData.syncHrPortal ?? true);
      setSendEmail(draftData.sendEmail ?? true);
      setEmailType(draftData.emailType || "Dotacion");

      // Procesar equipos y separar la Laptop del resto
      const equipos = draftData.equipos || [];
      const laptop = equipos.find(eq => eq.equipment_type === 'Laptop');
      const otherEquipos = equipos.filter(eq => eq.equipment_type !== 'Laptop');

      if (laptop) {
        setMainEquipo({
          equipment_type: laptop.equipment_type,
          manufacturer: laptop.manufacturer,
          model: laptop.model,
          serial_number: laptop.serial_number,
          hostname: laptop.hostname,
          purchase_cost: laptop.purchase_cost,
          quantity: laptop.quantity || 1,
          status: laptop.status,
          observation: laptop.observation || '',
          location: laptop.location,
        });
        setIncludeMain(true);
      } else {
        setIncludeMain(false);
      }

      // Procesar accesorios dinámicos
      const newAccesorios = otherEquipos.map(eq => ({
        type: eq.equipment_type,
        manufacturer: eq.manufacturer,
        model: eq.model || '',
        serial_number: eq.serial_number || '',
        purchase_cost: eq.purchase_cost,
        quantity: eq.quantity || 1,
        status: eq.status,
        observation: eq.observation || '',
      }));
      setAccesorios(newAccesorios);

      toast.success("Borrador cargado exitosamente");
    };

    // --- FLUJO DE CONTROL ---
    if (draftFromState) {
      // Si milagrosamente venía en el state, lo usamos directo
      procesarYAsignarBorrador(draftFromState);
    } else if (draftIdFromUrl) {
      // Como viene en la URL (?draftId=18), vamos a la API a traer el objeto pesado completo
      const cargarBorradorDesdeAPI = async () => {
        try {
          const fullDraft = await getDraft(draftIdFromUrl);
          procesarYAsignarBorrador(fullDraft);
        } catch (err) {
          console.error("Error al obtener detalle del borrador:", err);
          toast.error("No se pudo recuperar el detalle del borrador desde el servidor");
        }
      };
      cargarBorradorDesdeAPI();
    }
  }, [location.state, location.search]);

  const [draftId, setDraftId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false);
  const [generatedFiles, setGeneratedFiles] = useState([]);

  const [sendEmail, setSendEmail] = useState(true);
  const [emailType, setEmailType] = useState("Dotacion");
  const [syncHrPortal, setSyncHrPortal] = useState(true);
  const [autoSign, setAutoSign] = useState(false);

  const [taskStates, setTaskStates] = useState({
    pdf: "idle",
    email: "idle",
    sync: "idle",
    sign: "idle",
  });

  const toggleAccesorio = (t) =>
    setAccesorios((prev) => {
      if (prev.some((a) => a.type === t)) return prev.filter((a) => a.type !== t);
      const d = ACCESORIO_DEFAULTS[t];
      return [
        ...prev,
        {
          type: t,
          manufacturer: d.manufacturer ?? "",
          model: d.model ?? "",
          serial_number: "",
          purchase_cost: d.purchase_cost ?? 0,
          quantity: d.quantity ?? 1,
          status: "Nuevo",
          observation: "",
        },
      ];
    });

  const updateAccesorio = (t, patch) =>
    setAccesorios((prev) => prev.map((a) => (a.type === t ? { ...a, ...patch } : a)));

  const buildPayload = () => {
    const equipos = [];
    let id = 1;
    if (includeMain) equipos.push({ ...mainEquipo, id: id++, quantity: mainEquipo.quantity || 1 });
    accesorios.forEach((a) => {
      equipos.push({
        id: id++,
        equipment_type: a.type,
        quantity: a.quantity || 1,
        manufacturer: a.manufacturer,
        model: a.model || (a.type === "Mochila" ? "Genérico" : ""),
        serial_number: a.serial_number || "NA",
        purchase_cost: a.purchase_cost,
        hostname: a.hostname,
        status: a.status,
        observation: a.observation,
        location: mainEquipo.location,
      });
    });
    return {
      draft_id: draftId || undefined,
      equipos,
      usuario,
      syncHrPortal: syncHrPortal,
      marcar_firmada: autoSign,
      sendEmail: sendEmail,
      emailType: emailType
    };
  };

  const totalValor = useMemo(
    () =>
      (includeMain ? (mainEquipo.purchase_cost || 0) * (mainEquipo.quantity || 1) : 0) +
      accesorios.reduce((s, a) => s + (a.purchase_cost || 0) * (a.quantity || 1), 0),
    [includeMain, mainEquipo, accesorios],
  );

  const validate = () => {
    if (!usuario.username) return "Selecciona un colaborador antes de continuar.";
    const payload = buildPayload();
    if (payload.equipos.length === 0) return "Agrega al menos un equipo o accesorio.";

    // Validate main equipo
    if (includeMain) {
      if (!mainEquipo.manufacturer) return "La marca del equipo principal es obligatoria.";
      if (!mainEquipo.purchase_cost || mainEquipo.purchase_cost <= 0) return "El valor del equipo principal es obligatorio y debe ser mayor a 0.";
      if (!mainEquipo.status) return "El estado físico del equipo principal es obligatorio.";

      if (mainEquipo.equipment_type === "Laptop") {
        if (!mainEquipo.hostname) return "El hostname es obligatorio para Laptop.";
        if (!mainEquipo.serial_number) return "El número de serie es obligatorio para Laptop.";
        if (!mainEquipo.model) return "El modelo es obligatorio para Laptop.";
      } else if (mainEquipo.equipment_type === "Desktop") {
        if (!mainEquipo.model) return "El modelo es obligatorio para Desktop.";
      }
    }

    // Validate accesorios
    for (const acc of accesorios) {
      if (!acc.manufacturer) return `La marca del accesorio ${acc.type} es obligatoria.`;
      if (!acc.purchase_cost || acc.purchase_cost <= 0) return `El valor del accesorio ${acc.type} es obligatorio y debe ser mayor a 0.`;
      if (!acc.status) return `El estado físico del accesorio ${acc.type} es obligatorio.`;

      if (acc.type !== "Mochila" && !acc.model) return `El modelo del accesorio ${acc.type} es obligatorio.`;
    }

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

  const handleSaveDraft = async () => {
    const err = validate();
    if (err) {
      toast.error(err);
      return;
    }

    setSavingDraft(true);
    const payload = buildPayload();

    // Preparamos los datos tal como los espera el backend
    const draftPayload = {
      usuario: payload.usuario,
      equipos: payload.equipos,
      marcar_firmada: autoSign,
    };

    try {
      if (draftId) {
        // ACTUALIZAR: Si ya tenemos un ID en el estado, usamos el endpoint PUT
        await updateDraft(draftId, draftPayload);
        toast.success("Borrador actualizado correctamente");
      } else {
        // CREAR: Si no hay ID, es un borrador totalmente nuevo, usamos POST
        const response = await saveDraft(draftPayload);
        toast.success("Borrador guardado");

        // (Opcional pero recomendado) Si el backend te devuelve el ID del borrador recién creado,
        // lo guardamos en el estado. Así, si el usuario le da a "Guardar" de nuevo sin salir de la página,
        // actualizará el borrador en lugar de crear un clon.
        if (response && response.id) {
          setDraftId(response.id);
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error desconocido";
      toast.error("No se pudo guardar borrador", { description: msg });
    } finally {
      setSavingDraft(false);
    }
  };

  const runTasks = async (payload) => {
    // 1. Iniciamos los loaders visuales
    setTaskStates({
      pdf: "running",
      email: sendEmail ? "running" : "idle",
      sync: syncHrPortal ? "running" : "idle",
      sign: autoSign ? "running" : "idle",
    });

    try {
      // 2. Disparamos a la API real
      const result = await generateActa(payload);

      // Extraemos la estructura del JSON devuelto por tu Flask
      const resData = result?.data || result || {};

      // Evaluamos booleanos directos que manda el backend
      const syncExitosa = resData.sincronizacion?.exitosa === true;
      const emailExitoso = resData.email_enviado === true;

      // SOLUCIÓN AL BUG: Convertimos todo a mayúsculas para evitar el fallo de "Firmada" vs "FIRMADA"
      const estadoActa = String(resData.acta?.estado || "").toUpperCase();
      const firmaExitosa = estadoActa === "FIRMADA";

      // 4. Actualizamos el estado visual con precisión quirúrgica
      setTaskStates({
        pdf: "done", // Si no saltó al 'catch', el PDF y la DB fueron un éxito
        email: sendEmail ? (emailExitoso ? "done" : "error") : "idle",
        sync: syncHrPortal ? (syncExitosa ? "done" : "error") : "idle",
        sign: autoSign ? (firmaExitosa ? "done" : "error") : "idle",
      });

      return result;

    } catch (error) {
      // Si el servidor falla gravemente (Ej: 500 o ValidationError 400)
      // Todo lo que estaba en 'running' pasa a 'error'
      setTaskStates((s) => {
        const next = { ...s };
        Object.keys(next).forEach((k) => {
          if (next[k] === "running") next[k] = "error";
        });
        return next;
      });
      throw error;
    }
  };

  const handleConfirm = async () => {
    const payload = buildPayload();
    console.log("Payload a enviar:", payload);
    setConfirmOpen(false);
    setSubmitting(true);
    setTaskStates({ pdf: "idle", email: "idle", sync: "idle", sign: "idle" });

    try {
      // Esto asegura que si el usuario no guardó los cambios manualmente,
      // el backend de todas formas lea la base de datos actualizada.
      if (draftId) {
        await updateDraft(draftId, {
          usuario: payload.usuario,
          equipos: payload.equipos,
          marcar_firmada: autoSign,
        });
      }
      const result = await runTasks(payload);
      const docsGenerados = result?.data?.documents || result?.documents || [];
      setGeneratedFiles(docsGenerados);
      setSuccessOpen(true);
      toast.success("Acta generada correctamente", {
        description: `${payload.equipos.length} equipo(s) registrados para ${usuario.full_name}.`,
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Error desconocido";
      toast.error("No se pudo generar el acta", { description: msg });
      setTaskStates((s) => {
        const next = { ...s };
        Object.keys(next).forEach((k) => {
          if (next[k] === "running") next[k] = "idle";
        });
        return next;
      });
    } finally {
      setSubmitting(false);
    }
  };

  const resetAll = () => {
    setUsuario(EMPTY_USER);
    setMainEquipo(emptyMainEquipo());
    setIncludeMain(true);
    setAccesorios([]);
    setGeneratedFiles([]);
    setTaskStates({ pdf: "idle", email: "idle", sync: "idle", sign: "idle" });
    setSuccessOpen(false);
  };

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <ArrowLeft className="h-4 w-4" />
            </span>
            Actas de Entrega
          </Link>
          <Link
            to="/"
            className="rounded-full bg-secondary px-4 py-1.5 text-xs font-semibold text-secondary-foreground hover:bg-secondary/80"
          >
            Cancelar
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Generar Nueva Acta</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Complete los siguientes pasos para generar y registrar la nueva acta de entrega del
            equipamiento tecnológico.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <StepCard step={1} title="Colaborador & Automatización">
              <ColaboradorSearch usuario={usuario} onChange={setUsuario} />
              <div className="mt-5">
                <AutomationToggles
                  sendEmail={sendEmail}
                  setSendEmail={setSendEmail}
                  emailType={emailType}
                  setEmailType={setEmailType}
                  syncHrPortal={syncHrPortal}
                  setSyncHrPortal={setSyncHrPortal}
                  autoSign={autoSign}
                  setAutoSign={setAutoSign}
                />
              </div>
            </StepCard>

            <StepCard
              step={2}
              title="Equipo Principal"
              right={
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">Añadir equipo principal</span>
                  <Tooltip content="Si se incluye una Laptop, también se generará el Pagaré.">
                    <span className="inline-flex cursor-help items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 font-bold text-primary">
                      <Info className="h-3 w-3" /> GENERARÁ PAGARÉ
                    </span>
                  </Tooltip>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={includeMain}
                    onClick={() => setIncludeMain((v) => !v)}
                    className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition ${includeMain ? "bg-primary" : "bg-muted"
                      }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-background shadow transition ${includeMain ? "translate-x-4" : "translate-x-0.5"
                        }`}
                    />
                  </button>
                </div>
              }
            >
              {includeMain && <EquipoPrincipalForm equipo={mainEquipo} onChange={setMainEquipo} />}
            </StepCard>

            <StepCard step={3} title="Accesorios Dinámicos">
              <AccesoriosList items={accesorios} onToggle={toggleAccesorio} onUpdate={updateAccesorio} />
            </StepCard>
          </div>

          <div className="sticky top-20 self-start">
            <ResumenAccion
              usuario={usuario}
              mainType={includeMain ? mainEquipo.equipment_type : "—"}
              accesoriosCount={accesorios.length}
              flags={{ email: sendEmail, sync: syncHrPortal, autoSign }}
              taskStates={taskStates}
              onSubmit={onClickGenerate}
              isSubmitting={submitting}
              onSaveDraft={handleSaveDraft}
              savingDraft={savingDraft}
            />
          </div>
        </div>
      </main>

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title="Confirmar generación de acta"
        size="md"
        footer={
          <>
            <button
              type="button"
              onClick={() => setConfirmOpen(false)}
              className="rounded-full bg-muted px-4 py-1.5 text-sm font-semibold text-foreground hover:bg-muted/70"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              className="rounded-full bg-primary px-4 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90"
            >
              Confirmar y generar
            </button>
          </>
        }
      >
        <p className="text-sm text-muted-foreground">Estás por registrar el siguiente acta:</p>
        <ul className="mt-3 space-y-1.5 text-sm">
          <li><b>Colaborador:</b> {usuario.full_name} ({usuario.username})</li>
          <li>
            <b>Equipo principal:</b>{" "}
            {includeMain ? `${mainEquipo.equipment_type} ${mainEquipo.model || ""}`.trim() : "Ninguno"}
          </li>
          <li>
            <b>Accesorios:</b>{" "}
            {accesorios.length === 0 ? "Ninguno" : accesorios.map((a) => a.type).join(", ")}
          </li>
          <li><b>Valor total estimado:</b> ${totalValor.toFixed(2)}</li>
        </ul>
        <div className="mt-4 rounded-lg bg-muted/60 p-3 text-xs text-muted-foreground">
          <p className="mb-1 font-bold uppercase tracking-wider">Acciones automáticas</p>
          <ul className="list-disc pl-4">
            <li>
              Generar Acta{" "}
              {includeMain && mainEquipo.equipment_type === "Laptop" ? "+ Pagaré" : ""}
            </li>
            {sendEmail && <li>Enviar correo ({emailType}) a {usuario.full_name}</li>}
            {syncHrPortal && <li>Sincronizar con YoSoySaludsa</li>}
            {autoSign && <li>Marcar acta como firmada</li>}
          </ul>
        </div>
      </Modal>

      <Modal
        open={successOpen}
        onClose={() => setSuccessOpen(false)}
        title="Acta generada"
        size="lg"
        footer={
          <>
            <button
              type="button"
              onClick={() => setSuccessOpen(false)}
              className="rounded-full bg-muted px-4 py-1.5 text-sm font-semibold text-foreground hover:bg-muted/70"
            >
              Cerrar
            </button>
            <button
              type="button"
              onClick={resetAll}
              className="rounded-full bg-primary px-4 py-1.5 text-sm font-bold text-primary-foreground hover:bg-primary/90"
            >
              Generar otra
            </button>
          </>
        }
      >
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
            <CheckCircle2 className="h-6 w-6" />
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">
              ¡Listo! El acta fue registrada exitosamente.
            </p>
            <p className="text-xs text-muted-foreground">
              Se generaron los siguientes documentos para {usuario.full_name}.
            </p>
          </div>
        </div>

        {generatedFiles.length > 0 && (
          <ul className="mt-4 space-y-2">
            {generatedFiles.map((doc, index) => {
              const name = typeof doc === 'string'
                ? doc.split(/[\\/]/).pop()
                : doc.file_name || `Documento_${index + 1}.pdf`;

              // Creamos un key seguro
              const uniqueKey = typeof doc === 'string' ? doc : (doc.file_name || index);

              return (
                <li
                  key={uniqueKey}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/40 px-3 py-2 text-sm"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <FileText className="h-4 w-4 shrink-0 text-primary" />
                    <span className="truncate font-medium text-foreground">{name}</span>
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <Download className="h-3 w-3" /> .docx
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </Modal>
    </div>
  );
}
