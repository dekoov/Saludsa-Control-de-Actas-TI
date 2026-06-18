import React, { useState, useEffect } from 'react';
import { useNavigate } from "react-router-dom";
import { useSearchParams } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import Layout from "@/components/shared/Layout";
import HistorialSearch from "@/components/historial/HistorialSearch";
import HistorialFiltros from "@/components/historial/HistorialFiltros";
import HistorialTabs from "@/components/historial/HistorialTabs";
import ActasTable from "@/components/historial/ActasTable";
import BorradoresTable from "@/components/historial/BorradoresTable";
import { getHistorial, getDrafts, deleteDraft, getDashboardStats } from "@/lib/api"
import { useCallback } from 'react';

export default function Historial() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(() => {
    const tabParam = searchParams.get("tab");
    const soloAtencion = searchParams.get("solo_atencion");
    if (tabParam === "borradores") return "borradores";
    if (soloAtencion === "true") return "atencion";
    return "actas";
  });
  const [query, setQuery] = useState("");
  const [filtros, setFiltros] = useState(() => {
    const estadoParam = searchParams.get("estado");
    return {
      estado: estadoParam ? [estadoParam] : ['PENDIENTE_FIRMA', 'FIRMADA'],
      tipo: "",
      sync_status: "",
      tiene_pagare: "",
      fecha_desde: "",
      fecha_hasta: ""
    };
  });
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(() => {
    return !!searchParams.get("estado");
  });
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [columnasVisibles, setColumnasVisibles] = useState({ accesorios: true, pagare: true, sync: true });

  // Estados globales para mantener los contadores siempre vivos
  const [totalActas, setTotalActas] = useState(0);
  const [totalBorradores, setTotalBorradores] = useState(0);
  const [totalAtencion, setTotalAtencion] = useState(0);
  const [totalItems, setTotalItems] = useState(0);

  // 1. Función para cargar exclusivamente los contadores de los badges
  const fetchContadores = async () => {
    try {
      // Ejecutamos las 3 consultas en paralelo para máxima velocidad
      const [resActas, resAtencion, resBorradores] = await Promise.all([
        getHistorial({ page: 1, perPage: 1 }), // Total general de actas
        getHistorial({ page: 1, perPage: 1, activeTab: 'atencion' }),
        getDrafts() // Array de borradores
      ]);

      setTotalActas(resActas?.total || 0);
      setTotalAtencion(resAtencion?.total || 0);
      setTotalBorradores(resBorradores?.length || 0);
    } catch (err) {
      console.error("Error cargando contadores globales:", err);
    }
  };

  // 2. Función para cargar los datos específicos de la tabla seleccionada
  const fetchDatosTabla = useCallback(async () => {
    setLoading(true);
    try {
      if (activeTab === "borradores") {
        const borradores = await getDrafts();
        const listaFiltrada = query
          ? borradores.filter(b =>
            b.usuario?.full_name?.toLowerCase().includes(query.toLowerCase()) ||
            b.usuario?.username?.toLowerCase().includes(query.toLowerCase())
          )
          : borradores;

        setItems(listaFiltrada);
        setTotalBorradores(listaFiltrada.length);
        setTotalItems(listaFiltrada.length);
      } else {
        const resultado = await getHistorial({ page, perPage, query, activeTab, filtros });
        setItems(resultado?.items || []);
        setTotalItems(resultado?.total || 0);

        if (resultado?.perPageReal && resultado.perPageReal !== perPage) {
          setPerPage(resultado.perPageReal);
        }

        if (activeTab === "actas" && !query && Object.values(filtros).every(v => !v || v.length === 0)) {
          setTotalActas(resultado?.total || 0);
        }

        if (activeTab === "atencion" && !query && Object.values(filtros).every(v => !v || v.length === 0)) {
          setTotalAtencion(resultado?.total || 0);
        }
      }
    } catch (err) {
      toast.error("Error al cargar datos de la tabla");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [activeTab, query, page, perPage, filtros]);

  useEffect(() => {
    const fetchContadores = async () => {
      try {
        // En lugar de hacer 3 consultas pesadas de tablas,
        // pedimos los números pre-calculados a tu endpoint de estadísticas.
        const stats = await getDashboardStats();

        setTotalActas(stats?.total_actas || 0);
        setTotalAtencion(stats?.pendientes_saludsa || 0);
        setTotalBorradores(stats?.borradores || 0);
      } catch (err) {
        console.error("Error cargando contadores globales:", err);
      }
    };
    fetchContadores();
  }, []);

  // ÚNICO responsable de recargar la tabla. 
  useEffect(() => {
    fetchDatosTabla();
  }, [fetchDatosTabla]);

  const handleEliminarBorrador = async (id) => {
    if (!window.confirm("¿Está seguro de eliminar este borrador?")) return;
    try {
      await deleteDraft(id);
      toast.success("Borrador eliminado correctamente");
      fetchDatosTabla();
      fetchContadores();
    } catch (err) {
      toast.error("No se pudo eliminar el borrador");
    }
  };

  const handleCargarBorrador = (id) => {
    navigate(`/nueva-acta?draftId=${id}`);
  };

  return (
    <Layout>
      <div className="p-6">
        <h1 className="text-3xl font-bold mb-6">Historial de Actas</h1>
        <HistorialSearch
          onSearch={(q) => {
            // ESCUDO: Solo resetear si la búsqueda realmente cambió
            if (q !== query) {
              setQuery(q);
              setPage(1);
            }
          }}
          filtrosActivosCount={0}
          toggleFiltros={() => setFiltrosAbiertos(!filtrosAbiertos)}
        />
        <HistorialFiltros
          isOpen={filtrosAbiertos}
          filtros={filtros}
          setFiltros={setFiltros}
          onAplicar={() => { setPage(1) }}
          onLimpiar={() => setFiltros({ estado: [], tipo: "", sync_status: "", tiene_pagare: "", fecha_desde: "", fecha_hasta: "" })}
        />

        {/* Pasamos los contadores estables e independientes a los badges */}
        <HistorialTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          counts={{
            actas: totalActas,
            atencion: totalAtencion,
            borradores: totalBorradores
          }}
        />
        {loading ? (
          <div className="space-y-4/5 mt-4">
            {[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-gray-100 animate-pulse rounded-lg" />)}
          </div>
        ) : (
          <div className="mt-4">
            {activeTab === 'borradores' ? (
              <BorradoresTable
                data={items}
                onCargar={handleCargarBorrador}
                onEliminar={handleEliminarBorrador}
              />
            ) : (
              <ActasTable
                data={items}
                columnasVisibles={columnasVisibles}
                onRefreshRequired={() => {
                  fetchDatosTabla();
                  fetchContadores();
                }}
              />
            )}
            {totalItems > 0 && (
              <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
                <div className="text-sm text-muted-foreground">
                  Mostrando del <span className="font-medium">{(page - 1) * perPage + 1}</span> al <span className="font-medium">{(page - 1) * perPage + items.length}</span> de <span className="font-medium">{totalItems}</span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * perPage >= totalItems}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
