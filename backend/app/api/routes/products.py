import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Category, Product, Supplier
from app.models.user import User
from app.schemas.product import (
    CategoryResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


def _product_response(product: Product) -> ProductResponse:
    data = ProductResponse.model_validate(product)
    data.stock_status = product.stock_status
    return data


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Category).order_by(Category.name).all()


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category_id: int | None = None,
    supplier_id: int | None = None,
    stock_status: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Product).options(
        joinedload(Product.category), joinedload(Product.supplier)
    )

    if search:
        like = f"%{search}%"
        query = query.filter((Product.name.ilike(like)) | (Product.sku.ilike(like)))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    products = query.all()

    if stock_status:
        products = [p for p in products if p.stock_status == stock_status]

    reverse = sort_order == "desc"
    if sort_by == "stock":
        products.sort(key=lambda p: p.current_stock, reverse=reverse)
    elif sort_by == "price":
        products.sort(key=lambda p: float(p.unit_price), reverse=reverse)
    else:
        products.sort(key=lambda p: p.name.lower(), reverse=reverse)

    total = len(products)
    pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    items = products[start : start + page_size]

    return ProductListResponse(
        items=[_product_response(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.supplier))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_response(product)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "manager")),
):
    if db.query(Product).filter(Product.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=400, detail="Category not found")
    if not db.query(Supplier).filter(Supplier.id == data.supplier_id).first():
        raise HTTPException(status_code=400, detail="Supplier not found")

    product = Product(**data.model_dump())
    db.add(product)
    db.flush()
    db.add(Inventory(product_id=product.id, quantity=product.current_stock))
    db.commit()
    db.refresh(product)
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.supplier))
        .filter(Product.id == product.id)
        .first()
    )
    return _product_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "manager")),
):
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.supplier))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = data.model_dump(exclude_unset=True)
    if "sku" in updates and updates["sku"] != product.sku:
        if db.query(Product).filter(Product.sku == updates["sku"]).first():
            raise HTTPException(status_code=400, detail="SKU already exists")

    for field, value in updates.items():
        setattr(product, field, value)

    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    if inv:
        inv.quantity = product.current_stock

    db.commit()
    db.refresh(product)
    return _product_response(product)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
