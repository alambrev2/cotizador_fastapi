from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
import pandas as pd
from io import BytesIO
from sqlmodel import Session, select
from app.database import get_session
from app.models import Product
from openpyxl.styles import Font

router = APIRouter()


@router.post("/", response_model=Product)
def create_product(*, session: Session = Depends(get_session), product: Product):
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@router.get("/export")
def export_excel_route(session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    data = [{
        "Nombre del Producto": p.nombre,
        "Categoría": p.categoria or "",
        "Unidad de Medida": p.unidad_medida or "Pieza",
        "Marca": p.marca or "",
        "Proveedor": p.proveedor or "",
        "Costo de Compra ($)": float(p.costo or 0),
        "Precio Menudeo ($)": float(p.precio_menudeo or 0),
        "Precio Mayoreo ($)": float(p.precio_mayoreo or 0),
        "Cantidad Mínima para Mayoreo": int(p.cantidad_mayoreo or 12),
        "Inventario Inicial (Stock Actual)": int(p.stock or 0),
        "Inventario Mínimo de Alerta": int(p.stock_minimo or 5),
        "Estatus (Activo/Inactivo)": "Activo" if p.activo else "Inactivo",
        "Descripción técnica": p.descripcion or ""
    } for p in products]
    
    df = pd.DataFrame(data)
    io = BytesIO()
    with pd.ExcelWriter(io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Productos')
        worksheet = writer.sheets['Productos']
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
    
    return Response(
        content=io.getvalue(), 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={'Content-Disposition': 'attachment; filename="catalogo.xlsx"'}
    )

@router.get("/template")
def export_template_route():
    data = [{
        "Nombre del Producto": "Ejemplo Producto",
        "Categoría": "Herramientas",
        "Unidad de Medida": "Pieza",
        "Marca": "Generico",
        "Proveedor": "Distribuidor S.A.",
        "Costo de Compra ($)": 50.0,
        "Precio Menudeo ($)": 100.0,
        "Precio Mayoreo ($)": 80.0,
        "Cantidad Mínima para Mayoreo": 12,
        "Inventario Inicial (Stock Actual)": 10,
        "Inventario Mínimo de Alerta": 5,
        "Estatus (Activo/Inactivo)": "Activo",
        "Descripción técnica": "Ejemplo de especificaciones del producto"
    }]
    df = pd.DataFrame(data)
    io = BytesIO()
    with pd.ExcelWriter(io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla')
        worksheet = writer.sheets['Plantilla']
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
    
    return Response(
        content=io.getvalue(), 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={'Content-Disposition': 'attachment; filename="plantilla_productos.xlsx"'}
    )

@router.post("/import")
def import_excel_route(session: Session = Depends(get_session), file: UploadFile = File(...)):
    contents = file.file.read()
    df = pd.read_excel(BytesIO(contents))
    df = df.fillna("")
    
    count_new = 0
    count_updated = 0
    
    for _, row in df.iterrows():
        nombre = str(row.get('Nombre del Producto', '')).strip()
        if not nombre: continue
            
        precio_menudeo = float(row.get('Precio Menudeo ($)', 0) or 0)
        precio_mayoreo = float(row.get('Precio Mayoreo ($)', 0) or 0)
        costo = float(row.get('Costo de Compra ($)', 0) or 0)
        stock = int(row.get('Inventario Inicial (Stock Actual)', 0) or 0)
        stock_minimo = int(row.get('Inventario Mínimo de Alerta', 5) or 5)
        cantidad_mayoreo = int(row.get('Cantidad Mínima para Mayoreo', 12) or 12)
        marca = str(row.get('Marca', ''))
        categoria = str(row.get('Categoría', ''))
        unidad_medida = str(row.get('Unidad de Medida', 'Pieza'))
        proveedor = str(row.get('Proveedor', ''))
        descripcion = str(row.get('Descripción técnica', ''))
        
        # Procesar estatus seguro
        estatus_str = str(row.get('Estatus (Activo/Inactivo)', '')).strip().lower()
        activo = True
        if estatus_str == 'inactivo' or estatus_str == 'false' or estatus_str == '0':
            activo = False
        
        existing = session.exec(select(Product).where(Product.nombre == nombre)).first()
        if existing:
            existing.precio_menudeo = precio_menudeo
            existing.precio_mayoreo = precio_mayoreo
            existing.costo = costo
            existing.stock = stock
            existing.stock_minimo = stock_minimo
            existing.cantidad_mayoreo = cantidad_mayoreo
            if marca: existing.marca = marca
            if categoria: existing.categoria = categoria
            if proveedor: existing.proveedor = proveedor
            if descripcion: existing.descripcion = descripcion
            if unidad_medida: existing.unidad_medida = unidad_medida
            existing.activo = activo
            
            session.add(existing)
            count_updated += 1
        else:
            new_prod = Product(
                nombre=nombre,
                precio_menudeo=precio_menudeo,
                precio_mayoreo=precio_mayoreo,
                cantidad_mayoreo=cantidad_mayoreo,
                costo=costo,
                stock=stock,
                stock_minimo=stock_minimo,
                marca=marca,
                categoria=categoria,
                proveedor=proveedor,
                unidad_medida=unidad_medida,
                descripcion=descripcion,
                activo=activo
            )
            session.add(new_prod)
            count_new += 1
            
    session.commit()
    return {"message": f"Éxito: {count_new} creados, {count_updated} actualizados."}



@router.get("/", response_model=List[Product])
def read_products(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    search: str = None,
    brand: str = None,
):
    query = select(Product).order_by(Product.id.desc())
    if search:
        query = query.where(
            (Product.nombre.contains(search))
            | (Product.categoria.contains(search))
            | (Product.marca.contains(search))
        )
    if brand:
        query = query.where(Product.marca.contains(brand))

    products = session.exec(query.offset(offset).limit(limit)).all()
    return products


@router.get("/{product_id}", response_model=Product)
def read_product(*, session: Session = Depends(get_session), product_id: int):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=Product)
def update_product(
    *,
    session: Session = Depends(get_session),
    product_id: int,
    product_update: Product,
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_data = product_update.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(*, session: Session = Depends(get_session), product_id: int):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"ok": True}
