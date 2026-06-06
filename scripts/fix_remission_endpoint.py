path = 'app/api/v1/endpoints/payments.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '@router.get("/remission/{folio}")\ndef download_remission_by_folio('
new_func = '''@router.get("/remission/{folio}")
def download_remission_by_folio(
    folio: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin),
):
    """Regenera y descarga el PDF de una remision existente dado su folio."""
    import os
    from app.models import Customer

    # 1. Buscar cargos cargando la relacion cliente explicitamente
    cargos = session.exec(
        select(AccountCharge)
        .where(AccountCharge.folio_nota == folio)
        .options(selectinload(AccountCharge.cliente))
    ).all()
    if not cargos:
        raise HTTPException(status_code=404, detail=f"No se encontro la remision con folio {folio}")

    cliente = cargos[0].cliente or session.get(Customer, cargos[0].cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente de la remision no encontrado")

    nombre_safe = _safe_name(cliente.nombre)
    pdf_filename = f"Remision_{folio}_CLI{cliente.id:04d}_{nombre_safe}.pdf"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    reports_dir = os.path.join(BASE_DIR, "app", "static", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # 2. Buscar cualquier variante del PDF en disco
    existing = [f for f in os.listdir(reports_dir)
                if f.lower().startswith(f"remision_{folio.lower()}")]
    if existing:
        with open(os.path.join(reports_dir, existing[0]), "rb") as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f\'attachment; filename="{pdf_filename}"\'},
        )

    # 3. Regenerar desde BD
    total_remission = sum([float(c.monto) for c in cargos])
    try:
        html_content = templates.get_template("pdf/remission.html").render(
            cliente=cliente,
            cargos=cargos,
            total=total_remission,
            folio=folio,
        )
        pdf_bytes = generate_pdf_bytes(html_content)
        pdf_path = os.path.join(reports_dir, pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f\'attachment; filename="{pdf_filename}"\'},
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error regenerando PDF: {str(e)}")
'''

# Find and replace the old function block
old_decorator = '@router.get("/remission/{folio}")'
next_route     = '@router.post("/remission")'

idx_start = content.find(old_decorator)
idx_end   = content.find(next_route)

if idx_start == -1 or idx_end == -1:
    print("ERROR: markers not found")
else:
    new_content = content[:idx_start] + new_func + "\n" + content[idx_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("OK - block replaced successfully")
