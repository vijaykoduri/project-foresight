import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    InventoryAdjustRequest,
    InventoryItemResponse,
    InventorySummaryResponse,
    InventoryTransactionResponse,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=InventorySummaryResponse)
def get_inventory(
    stock_status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    products = (
        db.query(Product)
        .options(joinedload(Product.category))
        .filter(Product.status == "active")
        .all()
    )

    items = []
    counts = {"healthy": 0, "low_stock": 0, "out_of_stock": 0, "overstock": 0}
    total_value = 0.0

    for p in products:
        status = p.stock_status
        if status in counts:
            counts[status] += 1

        value = float(p.cost_price) * p.current_stock
        total_value += value

        item = InventoryItemResponse(
            product_id=p.id,
            sku=p.sku,
            name=p.name,
            category_name=p.category.name if p.category else "",
            current_stock=p.current_stock,
            minimum_stock=p.minimum_stock,
            maximum_stock=p.maximum_stock,
            reorder_point=p.reorder_point,
            unit_price=float(p.unit_price),
            cost_price=float(p.cost_price),
            inventory_value=round(value, 2),
            stock_status=status,
        )
        if stock_status is None or status == stock_status:
            items.append(item)

    return InventorySummaryResponse(
        total_inventory_value=round(total_value, 2),
        total_products=len(products),
        low_stock_count=counts["low_stock"],
        out_of_stock_count=counts["out_of_stock"],
        overstock_count=counts["overstock"],
        healthy_stock_count=counts["healthy"],
        items=items,
    )


@router.get("/{product_id}")
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    transactions = (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "product_id": product.id,
        "current_stock": product.current_stock,
        "stock_status": product.stock_status,
        "transactions": [
            InventoryTransactionResponse(
                id=t.id,
                product_id=t.product_id,
                product_name=product.name,
                product_sku=product.sku,
                transaction_type=t.transaction_type,
                quantity_change=t.quantity_change,
                quantity_before=t.quantity_before,
                quantity_after=t.quantity_after,
                reference=t.reference,
                notes=t.notes,
                created_at=t.created_at,
            )
            for t in transactions
        ],
    }


@router.post("/adjust")
def adjust_inventory(
    data: InventoryAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager", "user")),
):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    before = product.current_stock
    after = before + data.quantity_change
    if after < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock for this adjustment")

    product.current_stock = after
    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    if inv:
        inv.quantity = after

    tx = InventoryTransaction(
        product_id=product.id,
        transaction_type=data.transaction_type,
        quantity_change=data.quantity_change,
        quantity_before=before,
        quantity_after=after,
        reference=data.reference,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message": "Inventory adjusted successfully",
        "product_id": product.id,
        "quantity_before": before,
        "quantity_after": after,
    }


@router.get("/transactions/list", response_model=list[InventoryTransactionResponse])
def list_transactions(
    product_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(InventoryTransaction).order_by(InventoryTransaction.created_at.desc())
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)

    transactions = query.offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for t in transactions:
        product = db.query(Product).filter(Product.id == t.product_id).first()
        result.append(
            InventoryTransactionResponse(
                id=t.id,
                product_id=t.product_id,
                product_name=product.name if product else None,
                product_sku=product.sku if product else None,
                transaction_type=t.transaction_type,
                quantity_change=t.quantity_change,
                quantity_before=t.quantity_before,
                quantity_after=t.quantity_after,
                reference=t.reference,
                notes=t.notes,
                created_at=t.created_at,
            )
        )
    return result
