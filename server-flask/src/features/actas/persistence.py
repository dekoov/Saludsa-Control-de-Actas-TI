from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, or_
from src.infrastructure.persistence.db import db
from src.core.exceptions import DatabaseError
from src.features.employees.persistence import upsert_empleado
from src.features.equipments.persistence import insert_accesorio, upsert_activo
from src.models.acta import Acta
from src.models.employee import Empleado
from src.models.enums import ActaStatus, ActaType, SyncStatus
from src.models.equipment import Accesorio, Activo
from src.utils.parse_datetime import parse_utc_date


def _generate_acta_id() -> str:  # ← prefijo _ = internal
    """
    Genera un ID de acta secuencial en formato ACT-YYYYMMDD-NNN

    Returns:
        str: ID de acta generado (ej: ACT-20250515-001)
    """
    prefix = f"ACT-{datetime.now(UTC).strftime('%Y%m%d')}"
    last = (
        Acta.query.filter(Acta.id.like(f"{prefix}-%"))
        .order_by(Acta.id.desc())
        .with_for_update()
        .first()
    )
    n = (int(last.id.split("-")[-1]) + 1) if last else 1
    return f"{prefix}-{n:03d}"


def save_acta_to_database(
    equipos: list[dict[str, Any]],
    usuario: dict[str, Any],
    generated_docs: list[dict[str, Any]],
    estado: ActaStatus | None = None,
    sync_result: dict[str, Any] | None = None,
) -> str | None:
    """
    Guarda el acta en la base de datos después de la generación de documentos.
    Retorna el acta ID si exitoso, None si hubo error (no falla el request).
    Si no se proporciona estado, usa PENDIENTE_FIRMA por defecto.
    """
    try:
        empleado = upsert_empleado(usuario)

        # 2. Separar laptops y accesorios
        laptops = [eq for eq in equipos if eq.get("equipment_type") == "Laptop"]
        accesorios = [eq for eq in equipos if eq.get("equipment_type") != "Laptop"]

        activos_ids = []
        for laptop in laptops:
            activo = upsert_activo(laptop)
            activos_ids.append(activo.id)

        accesorios_ids = []
        for accesorio_data in accesorios:
            accesorio = insert_accesorio(accesorio_data)
            accesorios_ids.append(accesorio.id)

        tiene_pagare = len(laptops) > 0

        archivo_acta = generated_docs[0].get("docx_path") if generated_docs else None
        archivo_pagare = (
            generated_docs[1].get("docx_path") if len(generated_docs) > 1 else None
        )

        # Usar estado proporcionado o default a PENDIENTE_FIRMA
        acta_estado = estado if estado else ActaStatus.PENDIENTE_FIRMA

        # Handle sync status
        sincronizado_saludsa = False
        timestamp_sincronizacion = None
        estado_sincronizacion = SyncStatus.PENDIENTE

        if sync_result:
            sincronizado_saludsa = sync_result.get("exitosa", False)
            estado_sincronizacion = (
                SyncStatus.EXITOSA
                if sincronizado_saludsa
                else SyncStatus.FALLIDA
            )
            timestamp_sincronizacion = sync_result.get("timestamp")

        acta = Acta(  
            id=_generate_acta_id(),
            tipo=ActaType.DOTACION,
            estado=acta_estado,
            sincronizado_saludsa=sincronizado_saludsa,
            estado_sincronizacion=estado_sincronizacion,
            timestamp_sincronizacion=timestamp_sincronizacion,
            empleado_id=empleado.id,
            tiene_pagare=tiene_pagare,
            archivo_acta=archivo_acta,
            archivo_pagare=archivo_pagare,
        )

        db.session.add(acta)
        db.session.flush()

        # 6. Crear relaciones
        for activo_id in activos_ids:
            activo = Activo.query.get(activo_id)
            if activo is not None:
                acta.activos.append(activo)

        for accesorio_id in accesorios_ids:
            accesorio = Accesorio.query.get(accesorio_id)
            if accesorio is not None:
                acta.accesorios.append(accesorio)

        # 7. Commit
        db.session.commit()
        print(f"Acta {acta.id} guardada exitosamente en base de datos")
        return acta.id

    except Exception as e:
        db.session.rollback()
        raise DatabaseError(f"Error al guardar acta en base de datos: {e!s}") from e


def update_acta_status(acta_id: str, nuevo_estado: str) -> bool:
    """
    Modifica el estado de un acta directamente en la base de datos de forma segura.
    """
    try:
        acta = get_acta_by_id(acta_id)
        if not acta:
            return False

        acta.estado = nuevo_estado
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise DatabaseError(
            f"Error al actualizar el estado del acta {acta_id}: {e!s}"
        ) from e


def get_acta_by_id(acta_id: str) -> Acta | None:
    """
    Busca de forma limpia un acta por su identificador primario.
    """
    return Acta.query.get(acta_id)


def update_acta_document_paths(
    acta_id: str, archivo_acta: str, archivo_pagare: str | None = None
) -> bool:
    """
    Actualiza de forma atómica las rutas de los archivos físicos generados para un acta.
    """
    try:
        acta = get_acta_by_id(acta_id)
        if not acta:
            return False

        acta.archivo_acta = archivo_acta
        if archivo_pagare:
            acta.archivo_pagare = archivo_pagare

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise DatabaseError(
            f"Error al actualizar rutas de archivos del acta {acta_id}: {e!s}"
        ) from e


def get_paginated_actas_history(filters: dict[str, Any]):
    """
    Construye y ejecuta la consulta de actas en la base de datos aplicando filtros dinámicos.
    """
    query = Acta.query

    # Búsqueda Global
    search_query = filters.get("q")
    if search_query:
        search_term = f"%{search_query}%"
        query = (
            query.join(Empleado, Acta.empleado)
            .outerjoin(Acta.activos)
            .outerjoin(Acta.accesorios)
            .filter(
                or_(
                    Acta.id.ilike(search_term),
                    Empleado.full_name.ilike(search_term),
                    Empleado.username.ilike(search_term),
                    Activo.hostname.ilike(search_term),
                    Activo.serial_number.ilike(search_term),
                    Activo.manufacturer.ilike(search_term),
                    Activo.model.ilike(search_term),
                    Accesorio.serial_number.ilike(search_term),
                    Accesorio.manufacturer.ilike(search_term),
                    Accesorio.model.ilike(search_term),
                )
            )
        )

    estado = filters.get("estado")
    if estado:
        estados_lista = estado.split(",")
        query = query.filter(Acta.estado.in_(estados_lista))

    tipo = filters.get("tipo")
    if tipo:
        query = query.filter(Acta.tipo == tipo)

    solo_atencion = str(filters.get("solo_atencion", "")).lower() == "true"
    if solo_atencion:
        query = query.filter(
            or_(
                Acta.estado == "PENDIENTE_FIRMA",
                Acta.estado_sincronizacion.in_(
                    [SyncStatus.PENDIENTE.value, SyncStatus.FALLIDA.value]
                ),
            )
        )
    else:
        # Lógica tradicional de filtros individuales (Filtros comunes = AND)
        estado = filters.get("estado")
        if estado:
            estados_lista = estado.split(",")
            query = query.filter(Acta.estado.in_(estados_lista))

        sync_status = filters.get("sync_status")
        if sync_status:
            sync_str = str(sync_status).lower()
            if sync_str == "false":
                query = query.filter(
                    Acta.estado_sincronizacion.in_(
                        [SyncStatus.PENDIENTE.value, SyncStatus.FALLIDA.value]
                    )
                )
            elif sync_str == "true":
                query = query.filter(
                    Acta.estado_sincronizacion == SyncStatus.EXITOSA.value
                )
            else:
                for enum_item in SyncStatus:
                    if enum_item.value.lower() == sync_str:
                        query = query.filter(
                            Acta.estado_sincronizacion == enum_item.value
                        )
                        break
                else:
                    query = query.filter(Acta.estado_sincronizacion.ilike(sync_status))

    tiene_pagare = filters.get("tiene_pagare")
    if tiene_pagare is not None and tiene_pagare != "":
        es_pagare = str(tiene_pagare).lower() == "true"
        query = query.filter(Acta.tiene_pagare == es_pagare)

    # Filtro de Fechas
    fecha_desde = filters.get("fecha_desde")
    if fecha_desde:
        query = query.filter(Acta.fecha >= parse_utc_date(fecha_desde))

    fecha_hasta = filters.get("fecha_hasta")
    if fecha_hasta:
        query = query.filter(
            Acta.fecha <= parse_utc_date(fecha_hasta, is_end_of_day=True)
        )

    # Paginación segura
    page = max(1, filters.get("page", 1))
    per_page = max(1, min(filters.get("per_page", 20), 100))

    return query.order_by(desc(Acta.fecha)).paginate(
        page=page, per_page=per_page, error_out=False
    )


def update_acta_sync_status(
    acta_id: str, exitosa: bool, estado_sincronizacion: str
) -> bool:
    """
    Actualiza de forma segura los campos de sincronización con Saludsa en la base de datos.
    """
    try:
        acta = get_acta_by_id(acta_id)
        if not acta:
            return False

        acta.sincronizado_saludsa = exitosa
        acta.estado_sincronizacion = estado_sincronizacion
        acta.timestamp_sincronizacion = datetime.now(UTC)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise DatabaseError(
            f"Error al actualizar la sincronización del acta {acta_id}: {e!s}"
        ) from e
