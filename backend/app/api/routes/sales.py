import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from app.models.sales import Sale, SalesItem
from app.models.user import User
from app.schemas.sales import SaleCreate, SaleListResponse, SaleResponse, SaleItemResponse

router = APIRouter(prefix="/sales", tags=["Sales"])


def _sale_response(sale: Sale, db: Session) -> SaleResponse:
    items = []
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        items.append(
            SaleItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name if product else None,
                product_sku=product.sku if product else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
                line_total=float(item.line_total),
            )
        )
    return SaleResponse(
        id=sale.id,
        sale_number=sale.sale_number,
        customer_name=sale.customer_name,
        total_amount=float(sale.total_amount),
        total_units=sale.total_units,
        notes=sale.notes,
        sale_date=sale.sale_date,
        created_at=sale.created_at,
        items=items,
    )


@router.get("", response_model=SaleListResponse)
def list_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    product_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Sale).options(joinedload(Sale.items))

    if search:
        query = query.filter(
            (Sale.sale_number.ilike(f"%{search}%"))
            | (Sale.customer_name.ilike(f"%{search}%"))
        )
    if date_from:
        query = query.filter(Sale.sale_date >= date_from)
    if date_to:
        query = query.filter(Sale.sale_date <= date_to)
    if product_id:
        query = query.join(SalesItem).filter(SalesItem.product_id == product_id)

    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    sales = (
        query.order_by(Sale.sale_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return SaleListResponse(
        items=[_sale_response(s, db) for s in sales],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sale = db.query(Sale).options(joinedload(Sale.items)).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return _sale_response(sale, db)


@router.post("", response_model=SaleResponse, status_code=201)
def create_sale(
    data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager", "user")),
):
    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.current_stock}, Requested: {item.quantity}",
            )

    sale_number = f"SALE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    sale = Sale(
        sale_number=sale_number,
        customer_name=data.customer_name,
        notes=data.notes,
        created_by=current_user.id,
        sale_date=datetime.now(timezone.utc),
    )
    db.add(sale)
    db.flush()

    total_amount = 0.0
    total_units = 0

    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        line_total = float(product.unit_price) * item_data.quantity
        sale_item = SalesItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=float(product.unit_price),
            line_total=line_total,
        )
        db.add(sale_item)

        before = product.current_stock
        product.current_stock = before - item_data.quantity
        inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
        if inv:
            inv.quantity = product.current_stock

        tx = InventoryTransaction(
            product_id=product.id,
            transaction_type="sale",
            quantity_change=-item_data.quantity,
            quantity_before=before,
            quantity_after=product.current_stock,
            reference=sale_number,
            notes=f"Sale {sale_number}",
            created_by=current_user.id,
        )
        db.add(tx)

        total_amount += line_total
        total_units += item_data.quantity

    sale.total_amount = total_amount
    sale.total_units = total_units
    db.commit()
    db.refresh(sale)
    sale = db.query(Sale).options(joinedload(Sale.items)).filter(Sale.id == sale.id).first()
    return _sale_response(sale, db)
