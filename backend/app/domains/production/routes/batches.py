from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.database import get_session
from app.domains.auth.dependencies import get_current_user
from app.domains.auth.models import User
from app.domains.production.schemas import (
    BatchCreate,
    BatchItemRead,
    BatchRead,
    BatchStatusUpdate,
    BlockRead,
    LinkedOrderRead,
    MasterSheetResponse,
)
from app.domains.production.services import ProductionService

router = APIRouter(prefix="/production/batches", tags=["production"])

_svc = ProductionService()


def _build_batch_read(svc: ProductionService, session: Session, batch) -> BatchRead:
    from app.domains.production.repositories import (
        ProductionBatchItemRepository,
        ProductionBatchSalesOrderRepository,
        ProductionBlockRepository,
    )

    items_raw = ProductionBatchItemRepository(session).list_by_batch_id(batch.id)
    links_raw = ProductionBatchSalesOrderRepository(session).list_by_batch_id(batch.id)
    block_repo = ProductionBlockRepository(session)

    items = []
    for bi in items_raw:
        blocks_raw = block_repo.list_by_batch_item_id(bi.id)
        items.append(
            BatchItemRead(
                id=bi.id,
                product_id=bi.product_id,
                required_qty_total=bi.required_qty_total,
                available_stock_qty=bi.available_stock_qty,
                to_produce_qty=bi.to_produce_qty,
                produced_qty=bi.produced_qty,
                blocks=[BlockRead.model_validate(b) for b in blocks_raw],
            )
        )

    linked = [
        LinkedOrderRead(
            sales_order_id=lnk.sales_order_id,
            link_mode=str(lnk.link_mode),
        )
        for lnk in links_raw
    ]

    return BatchRead(
        public_id=batch.public_id,
        kind=batch.kind,
        status=batch.status,
        name=batch.name,
        notes=batch.notes,
        cutoff_at=batch.cutoff_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        items=items,
        linked_orders=linked,
    )


# Register fixed-path routes BEFORE /{public_id} to avoid UUID path conflict

@router.post("/cutoff", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def cutoff(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.cutoff(session, created_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


@router.get("", response_model=list[BatchRead])
def list_batches(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[BatchRead]:
    batches = _svc.list_batches(session)
    return [_build_batch_read(_svc, session, b) for b in batches]


@router.post("", response_model=BatchRead, status_code=status.HTTP_201_CREATED)
def create_batch(
    data: BatchCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.create_batch(session, data, created_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


@router.get("/{public_id}", response_model=BatchRead)
def get_batch(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> BatchRead:
    batch = _svc.get_batch(session, public_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return _build_batch_read(_svc, session, batch)


@router.patch("/{public_id}/status", response_model=BatchRead)
def update_batch_status(
    public_id: UUID,
    data: BatchStatusUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BatchRead:
    try:
        batch = _svc.update_status(session, public_id, data, performed_by=current_user.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _build_batch_read(_svc, session, batch)


def _generate_master_sheet_pdf(sheet: MasterSheetResponse, user: User) -> bytes:
    """Build a ReportLab PDF for the master sheet and return raw bytes."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        KeepTogether,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    PAGE_W, _ = A4
    MARGIN = 2 * cm

    user_name = f"{user.first_name} {user.last_name}".strip() or user.email
    print_date = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # ── Styles ──────────────────────────────────────────────────────────────
    s_title = ParagraphStyle(
        "s_title", fontName="Helvetica-Bold", fontSize=16, spaceAfter=4
    )
    s_sub = ParagraphStyle(
        "s_sub", fontName="Helvetica", fontSize=9, textColor=colors.grey, spaceAfter=2
    )
    s_item_h = ParagraphStyle(
        "s_item_h", fontName="Helvetica-Bold", fontSize=11, spaceBefore=10, spaceAfter=2
    )
    s_item_s = ParagraphStyle(
        "s_item_s", fontName="Helvetica", fontSize=9, textColor=colors.grey, spaceAfter=6
    )
    s_section = ParagraphStyle(
        "s_section",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.grey,
        spaceBefore=6,
        spaceAfter=3,
    )
    s_warn = ParagraphStyle(
        "s_warn",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.red,
        spaceBefore=6,
        spaceAfter=3,
    )

    # ── Footer callback ──────────────────────────────────────────────────────
    def _draw_footer(canvas, doc):  # noqa: ANN001
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            PAGE_W / 2,
            MARGIN * 0.45,
            f"Impreso el {print_date}  ·  Generado por {user_name}  ·  Página {doc.page}",
        )
        canvas.restoreState()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN * 1.4,
    )

    story = []

    # ── Document header ──────────────────────────────────────────────────────
    batch_name = sheet.name or "Batch sin nombre"
    cutoff_str = ""
    if sheet.cutoff_at:
        cutoff_str = f"  ·  Corte: {sheet.cutoff_at.strftime('%d/%m/%Y %H:%M')}"

    story.append(Paragraph("Hoja Maestra de Producción", s_title))
    story.append(
        Paragraph(
            f"{batch_name}{cutoff_str}  ·  Tipo: {sheet.kind}  ·  Estado: {sheet.status}",
            s_sub,
        )
    )
    story.append(
        HRFlowable(
            width="100%", thickness=1, color=colors.lightgrey, spaceBefore=6, spaceAfter=12
        )
    )

    if not sheet.items:
        story.append(Paragraph("Sin items en este batch.", s_sub))

    # ── Items ────────────────────────────────────────────────────────────────
    for item in sheet.items:
        block_els = []

        # Item title + quantities
        block_els.append(
            Paragraph(f"{item.product_sku}  —  {item.product_name}", s_item_h)
        )
        block_els.append(
            Paragraph(
                f"Requerido: {item.required_qty_total}  ·  "
                f"En stock: {item.available_stock_qty}  ·  "
                f"A producir: {item.to_produce_qty}  ·  "
                f"Producido: {item.produced_qty}",
                s_item_s,
            )
        )

        # FALTANTES (unresolved blocks)
        unresolved = [b for b in item.blocks if b.resolved_at is None]
        if unresolved:
            block_els.append(Paragraph("⚠  FALTANTES DE COMPONENTES", s_warn))
            b_data = [["Componente ID", "Cantidad faltante"]]
            for blk in unresolved:
                b_data.append([f"#{blk.component_id}", str(blk.missing_qty)])

            avail_w = PAGE_W - 2 * MARGIN
            b_tbl = Table(b_data, colWidths=[avail_w * 0.6, avail_w * 0.4])
            b_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.red),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.HexColor("#fff0f0"), colors.white],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ffcccc")),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            block_els.append(b_tbl)
            block_els.append(Spacer(1, 6))

        # BOM table
        if item.bom:
            block_els.append(Paragraph("BOM — Lista de materiales", s_section))
            bom_data = [["Componente", "SKU", "× Kit", "Total", "Disponible", "Falta"]]
            for b in item.bom:
                bom_data.append(
                    [
                        b.component_name,
                        b.component_sku,
                        str(b.qty_per_kit),
                        str(b.total_needed),
                        str(b.available),
                        str(b.missing) if b.missing > 0 else "—",
                    ]
                )

            avail_w = PAGE_W - 2 * MARGIN
            col_w = [avail_w * 0.35, avail_w * 0.19, avail_w * 0.1, avail_w * 0.1, avail_w * 0.13, avail_w * 0.13]
            bom_tbl = Table(bom_data, colWidths=col_w)

            ts = TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#fafafa")],
                    ),
                ]
            )
            for row_idx, b in enumerate(item.bom, start=1):
                if b.missing > 0:
                    ts.add("TEXTCOLOR", (5, row_idx), (5, row_idx), colors.red)
                    ts.add("FONTNAME", (5, row_idx), (5, row_idx), "Helvetica-Bold")

            bom_tbl.setStyle(ts)
            block_els.append(bom_tbl)

        block_els.append(Spacer(1, 8))
        block_els.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#e5e7eb"),
                spaceAfter=4,
            )
        )
        story.append(KeepTogether(block_els))

    doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return buffer.getvalue()


@router.get("/{public_id}/master-sheet/pdf")
def get_master_sheet_pdf(
    public_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    try:
        sheet = _svc.get_master_sheet(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    pdf_bytes = _generate_master_sheet_pdf(sheet, current_user)
    filename = f"hoja-maestra-{str(public_id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


def _truncate_text(text: str, max_width: float, font_name: str, font_size: float, c) -> str:  # noqa: ANN001
    """Shorten *text* with an ellipsis so it fits inside *max_width* points."""
    if c.stringWidth(text, font_name, font_size) <= max_width:
        return text
    while text and c.stringWidth(text + "…", font_name, font_size) > max_width:
        text = text[:-1]
    return (text + "…") if text else "…"


def _draw_content_slip(  # noqa: PLR0913
    c,  # noqa: ANN001
    x: float,
    y: float,
    w: float,
    h: float,
    kit_name: str,
    kit_sku: str,
    bom: list,
) -> None:
    """Draw one tirilla inside the rectangle (x, y, w, h) — origin at bottom-left."""
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import cm

    PAD = 0.15 * cm

    # ── Dashed border (cut mark) ─────────────────────────────────────────────
    c.saveState()
    c.setDash(4, 4)
    c.setStrokeColor(rl_colors.HexColor("#bbbbbb"))
    c.setLineWidth(0.4)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.restoreState()

    inner_w = w - 2 * PAD

    # cy tracks the current writing position (descending from top)
    cy = y + h

    # ── Kit name ─────────────────────────────────────────────────────────────
    TITLE_FONT = "Helvetica-Bold"
    TITLE_SIZE = 8.0
    TITLE_LEAD = 10.0
    cy -= PAD + TITLE_LEAD

    c.setFont(TITLE_FONT, TITLE_SIZE)
    c.setFillColor(rl_colors.black)
    c.drawString(x + PAD, cy, _truncate_text(kit_name, inner_w, TITLE_FONT, TITLE_SIZE, c))

    # ── SKU ──────────────────────────────────────────────────────────────────
    SKU_SIZE = 5.5
    cy -= SKU_SIZE + 3
    c.setFont("Helvetica", SKU_SIZE)
    c.setFillColor(rl_colors.HexColor("#888888"))
    c.drawString(x + PAD, cy, kit_sku)

    # ── Separator ────────────────────────────────────────────────────────────
    cy -= 4
    c.setStrokeColor(rl_colors.HexColor("#dddddd"))
    c.setLineWidth(0.3)
    c.line(x + PAD, cy, x + w - PAD, cy)
    cy -= 5

    # ── QR placeholder — reserved in the bottom-right corner ─────────────────
    QR_SIZE = 1.1 * cm
    qr_x = x + w - QR_SIZE - PAD
    qr_y = y + PAD

    # ── Components ───────────────────────────────────────────────────────────
    COMP_SIZE = 6.0
    COMP_LEAD = 7.5
    min_cy = qr_y + QR_SIZE + 3  # keep clear of QR box

    for bom_item in bom:
        if cy - COMP_LEAD < min_cy:
            c.setFont("Helvetica", COMP_SIZE - 1)
            c.setFillColor(rl_colors.HexColor("#aaaaaa"))
            cy -= COMP_LEAD
            c.drawString(x + PAD, cy, "…")
            break

        qty_str = f"×{bom_item.qty_per_kit}"
        qty_w = c.stringWidth(qty_str, "Helvetica-Bold", COMP_SIZE)
        name_max_w = inner_w - qty_w - 4
        name = _truncate_text(
            f"• {bom_item.component_name}", name_max_w, "Helvetica", COMP_SIZE, c
        )

        cy -= COMP_LEAD
        c.setFont("Helvetica", COMP_SIZE)
        c.setFillColor(rl_colors.HexColor("#222222"))
        c.drawString(x + PAD, cy, name)

        c.setFont("Helvetica-Bold", COMP_SIZE)
        c.setFillColor(rl_colors.HexColor("#444444"))
        c.drawRightString(x + w - PAD, cy, qty_str)

    # ── QR placeholder box ────────────────────────────────────────────────────
    c.saveState()
    c.setFillColor(rl_colors.HexColor("#f5f5f5"))
    c.setStrokeColor(rl_colors.HexColor("#cccccc"))
    c.setLineWidth(0.4)
    c.rect(qr_x, qr_y, QR_SIZE, QR_SIZE, stroke=1, fill=1)
    c.setFont("Helvetica", 4.5)
    c.setFillColor(rl_colors.HexColor("#aaaaaa"))
    c.drawCentredString(qr_x + QR_SIZE / 2, qr_y + QR_SIZE / 2 - 2, "QR")
    c.restoreState()


def _generate_content_slips_pdf(sheet: MasterSheetResponse, copies_per_kit: int) -> bytes:
    """
    Lay out N content slips per A4 page in a 3×3 grid.

    Each slip shows kit name, SKU, BOM component list and a QR placeholder.
    copies_per_kit controls how many identical slips are printed per kit unit.
    """
    import math

    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as rl_canvas

    PAGE_W, PAGE_H = A4
    MARGIN = 0.5 * cm
    GUTTER = 0.25 * cm
    COLS = 3
    ROWS = 3
    SLIPS_PER_PAGE = COLS * ROWS

    slip_w = (PAGE_W - 2 * MARGIN - (COLS - 1) * GUTTER) / COLS
    slip_h = (PAGE_H - 2 * MARGIN - (ROWS - 1) * GUTTER) / ROWS

    # Build the flat list of slips — grouped by kit (items already ordered)
    slips: list[tuple[str, str, list]] = []
    for item in sheet.items:
        qty = item.to_produce_qty
        if qty <= 0:
            continue
        for _ in range(qty * copies_per_kit):
            slips.append((item.product_name, item.product_sku, item.bom))

    buffer = BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)

    if not slips:
        c.setFont("Helvetica", 10)
        c.setFillColor(rl_colors.grey)
        c.drawCentredString(
            PAGE_W / 2,
            PAGE_H / 2,
            "No hay kits a producir en este batch.",
        )
        c.save()
        return buffer.getvalue()

    total_pages = math.ceil(len(slips) / SLIPS_PER_PAGE)

    for page_idx in range(total_pages):
        page_slips = slips[page_idx * SLIPS_PER_PAGE : (page_idx + 1) * SLIPS_PER_PAGE]

        for slip_idx, (kit_name, kit_sku, bom) in enumerate(page_slips):
            col = slip_idx % COLS
            row = slip_idx // COLS
            x = MARGIN + col * (slip_w + GUTTER)
            # ReportLab origin is bottom-left; row 0 is the topmost strip
            y = PAGE_H - MARGIN - (row + 1) * slip_h - row * GUTTER
            _draw_content_slip(c, x, y, slip_w, slip_h, kit_name, kit_sku, bom)

        if page_idx < total_pages - 1:
            c.showPage()

    c.save()
    return buffer.getvalue()


@router.get("/{public_id}/content-slips/pdf")
def get_content_slips_pdf(
    public_id: UUID,
    copies_per_kit: int = Query(default=1, ge=1, le=20),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    try:
        sheet = _svc.get_master_sheet(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    pdf_bytes = _generate_content_slips_pdf(sheet, copies_per_kit)
    filename = f"tirillas-{str(public_id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/{public_id}/master-sheet", response_model=MasterSheetResponse)
def get_master_sheet(
    public_id: UUID,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> MasterSheetResponse:
    try:
        return _svc.get_master_sheet(session, public_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
