// api.js

const BASE_URL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:5000";

const MOCK_USERS = [
  {
    full_name: "CORREA BELTRAN DAVID LEANDRO",
    username: "dcorrea",
    national_id: "1726354471",
    city: "UIO",
    position: "PASANTE",
    department: "TI",
  }
];

export async function searchADUsers(query) {
  if (!query || query.trim().length < 2) return [];
  try {
    const res = await fetch(
      `${BASE_URL}/api/ad/users?q=${encodeURIComponent(query)}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
        credentials: "include" // 
      },
    );
    if (!res.ok) throw new Error(`AD search failed: ${res.status}`);
    const data = await res.json();
    return data.usuarios ?? [];
  } catch (err) {
    console.warn("[api] AD fetch falló, usando mock:", err);
    const q = query.toLowerCase();
    return MOCK_USERS.filter(
      (u) =>
        u.full_name.toLowerCase().includes(q) ||
        u.username.toLowerCase().includes(q) ||
        u.national_id.includes(q),
    );
  }
}

export function adUserToUsuario(u) {
  return {
    username: u.username,
    full_name:
      u.full_name ||
      u.display_name ||
      `${u.first_names ?? ""} ${u.last_names ?? ""}`.trim(),
    national_id: u.national_id,
    city: u.city,
  };
}

export async function generateDiscount(payload) {
  const res = await fetch(`${BASE_URL}/api/discounts/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include"
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.message || `Error ${res.status}`);
  }

  const response = await res.json();
  const doc = response.data; // Aquí Flask envuelve tu data en el success_response

  try {
    // Decodificación Base64 idéntica a generateActa
    const byteCharacters = atob(doc.pdf_base64);
    const byteNumbers = new Uint8Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const blob = new Blob([byteNumbers], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);

    const newWindow = window.open(url, "_blank");
    if (!newWindow) alert("Permite los pop-ups para ver el PDF.");

    return { filename: doc.file_name };
  } catch (err) {
    throw new Error("Error al procesar el archivo en el navegador");
  }
}

export async function generateActa(payload) {
  const res = await fetch(`${BASE_URL}/api/actas/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include" // <-- CORRECCIÓN: Envía la cookie
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const detail = errorData?.detalle || errorData?.error || `HTTP ${res.status}`;
    throw new Error(detail);
  }

  const data = await res.json();

  const list_documents = data?.data?.documents || data?.documents;
  if (!list_documents || !Array.isArray(list_documents)) {
    console.error("No se encontró el array de documentos en la respuesta.", data);
    alert("Error de comunicación: El servidor no devolvió los documentos correctamente.");
    return data;
  }

  list_documents.forEach((doc) => {
    try {
      const byteCharacters = atob(doc.pdf_base64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);

      const blob = new Blob([byteArray], { type: "application/pdf" });

      const url = window.URL.createObjectURL(blob);
      const newWindow = window.open(url, "_blank");
      if (!newWindow) {
        alert(`No se pudo abrir la nueva ventana para ${doc.file_name}. Por favor, permita pop-ups para este sitio.`);
      }
    } catch (err) {
      console.error(`Error al procesar el documento ${doc.file_name}:`, err);
    }
  });

  return data;
}

// GET /api/dashboard/stats
export async function getDashboardStats() {
  const res = await fetch(`${BASE_URL}/api/dashboard/stats`, { credentials: "include" }); // <-- CORRECCIÓN
  if (!res.ok) throw new Error(`Stats fetch failed: ${res.status}`);
  const payload = await res.json();
  return payload.data;
}

// GET /api/dashboard/recent-users
export async function getRecentUsers() {
  const res = await fetch(`${BASE_URL}/api/dashboard/recent-users`, { credentials: "include" }); // <-- CORRECCIÓN
  if (!res.ok) throw new Error(`Recent users fetch failed: ${res.status}`);
  const payload = await res.json();
  return payload.data;
}

// GET /api/actas/historial con Filtros y Paginación Dinámica
export async function getHistorial({ page = 1, perPage = 20, query = "", activeTab = "actas", filtros = {} } = {}) {
  try {
    const params = new URLSearchParams();
    params.append("page", page);
    params.append("per_page", perPage);

    if (query) params.append("q", query);

    // Lógica de pestañas y estados
    if (activeTab === 'atencion') {
      params.append("solo_atencion", "true"); // <-- Cambiamos los dos appends anteriores por este
    } else {
      // Estos filtros solo se aplican si no estamos en la pestaña fija de atención
      if (filtros.estado && filtros.estado.length > 0) {
        const estadoVal = Array.isArray(filtros.estado) ? filtros.estado.join(',') : filtros.estado;
        params.append("estado", estadoVal);
      }

      if (filtros.sync_status) {
        const statusMap = { "EXITO": "exitosa", "ERROR": "fallida", "PENDIENTE": "pendiente" };
        params.append("sync_status", statusMap[filtros.sync_status] || filtros.sync_status);
      }
    }

    // Filtros adicionales
    if (filtros.tipo) params.append("tipo", filtros.tipo);

    // Mapeo para que coincida con lo que espera la base de datos ('exitosa', 'fallida', 'pendiente')
    if (filtros.sync_status) {
      const statusMap = { "EXITO": "exitosa", "ERROR": "fallida", "PENDIENTE": "pendiente" };
      params.append("sync_status", statusMap[filtros.sync_status] || filtros.sync_status);
    }

    // CORRECCIÓN: Validar explícitamente que no sea vacío ni indefinido para que acepte "false"
    if (filtros.tiene_pagare !== "" && filtros.tiene_pagare !== undefined) {
      params.append("tiene_pagare", filtros.tiene_pagare);
    }

    if (filtros.fecha_desde) params.append("fecha_desde", filtros.fecha_desde);
    if (filtros.fecha_hasta) params.append("fecha_hasta", filtros.fecha_hasta);

    const res = await fetch(`${BASE_URL}/api/actas/historial?${params.toString()}`, {
      credentials: "include"
    });

    if (!res.ok) throw new Error(`Historial fetch failed: ${res.status}`);

    const payload = await res.json();

    return {
      items: payload.data?.items || [],
      total: payload.data?.total || 0,
      perPageReal: payload.data?.per_page
    };
  } catch (err) {
    console.error("[api] getHistorial falló:", err);
    throw err;
  }
}

// POST /api/drafts
export async function saveDraft(payload) {
  const res = await fetch(`${BASE_URL}/api/drafts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include", // <-- CORRECCIÓN
  });
  if (!res.ok) throw new Error(`Save draft failed: ${res.status}`);
  return res.json();
}

// GET /api/drafts
export async function getDrafts() {
  const res = await fetch(`${BASE_URL}/api/drafts`, { credentials: "include" }); // <-- CORRECCIÓN
  if (!res.ok) throw new Error(`Get drafts failed: ${res.status}`);
  return res.json();
}

// GET /api/drafts/<id>
export async function getDraft(id) {
  const res = await fetch(`${BASE_URL}/api/drafts/${id}`, { credentials: "include" }); // <-- CORRECCIÓN
  if (!res.ok) throw new Error(`Get draft failed: ${res.status}`);
  return res.json();
}

// DELETE /api/drafts/<id>
export async function deleteDraft(id) {
  const res = await fetch(`${BASE_URL}/api/drafts/${id}`, {
    method: "DELETE",
    credentials: "include", // <-- CORRECCIÓN
  });
  if (!res.ok) throw new Error(`Delete draft failed: ${res.status}`);
  return res.json();
}

/**
 * Obtiene el PDF de un documento (acta o pagare) desde el stream del servidor
 * y lo abre en una nueva pestaña del navegador usando Blobs.
 * * @param {string} actaId - ID del acta (ej: 'ACT-20260608-001')
 * @param {'acta' | 'pagare'} docType - Tipo de archivo a descargar
 */
export async function downloadActaDocumentPDF(actaId, docType) {
  try {
    const res = await fetch(`${BASE_URL}/api/actas/${actaId}/documents/${docType}/pdf`, {
      method: "GET",
      credentials: "include"
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.message || `Error HTTP ${res.status}`);
    }
    const pdfBlob = await res.blob();
    const blobUrl = window.URL.createObjectURL(pdfBlob);
    const newWindow = window.open(blobUrl, "_blank");
    if (!newWindow) alert("Por favor, habilite los pop-ups para ver el archivo.");
    return true;
  } catch (err) {
    console.error(`[api] Error en descarga (${docType}):`, err);
    throw err;
  }
}

// 2. PATCH /api/actas/:id/firmar
export async function marcarActaComoFirmada(actaId) {
  const res = await fetch(`${BASE_URL}/api/actas/${actaId}/firmar`, {
    method: "PATCH",
    credentials: "include"
  });
  if (!res.ok) throw new Error("No se pudo marcar como firmada.");
  return await res.json();
}

// 3. POST /api/actas/:id/sync
export async function reintentarSyncActa(actaId) {
  const res = await fetch(`${BASE_URL}/api/actas/${actaId}/sync`, {
    method: "POST",
    credentials: "include"
  });
  if (!res.ok) throw new Error("Falló el reintento de sincronización.");
  return await res.json();
}

// 4. PATCH /api/actas/:id/anular
export async function anularActa(actaId) {
  const res = await fetch(`${BASE_URL}/api/actas/${actaId}/anular`, {
    method: "PATCH",
    credentials: "include"
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData?.message || "No se pudo anular el acta.");
  }
  return await res.json();
}

// PUT /api/drafts/<id>
export async function updateDraft(id, payload) {
  const res = await fetch(`${BASE_URL}/api/drafts/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  if (!res.ok) throw new Error(`Update draft failed: ${res.status}`);
  return res.json();
}
