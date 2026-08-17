import { useEffect, useState, useCallback } from 'react';
import { productsApi, suppliersApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { useAuth } from '../context/AuthContext';
import { formatCurrency, formatNumber } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Modal from '../components/common/Modal';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCatId, setSelectedCatId] = useState('');
  const { isManager, isAdmin } = useAuth();
  const { addNotification } = useNotification();

  // Create Product Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editProduct, setEditProduct] = useState(null); // Null for add, product object for edit
  const [sku, setSku] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [catId, setCatId] = useState('');
  const [supId, setSupId] = useState('');
  const [price, setPrice] = useState('');
  const [cost, setCost] = useState('');
  const [stock, setStock] = useState('');
  const [minStock, setMinStock] = useState('');
  const [maxStock, setMaxStock] = useState('');
  const [reorderPt, setReorderPt] = useState('');
  const [reorderQty, setReorderQty] = useState('');
  const [leadTime, setLeadTime] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      const params = { limit: 100 };
      if (search) params.search = search;
      if (selectedCatId) params.category_id = parseInt(selectedCatId);
      
      const res = await productsApi.list(params);
      setProducts(res.data.items || []);
    } catch {
      addNotification('Error loading products', 'error');
    } finally {
      setLoading(false);
    }
  }, [search, selectedCatId, addNotification]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [catRes, supRes] = await Promise.all([
          productsApi.categories(),
          suppliersApi.list({ limit: 100 })
        ]);
        setCategories(catRes.data || []);
        setSuppliers(supRes.data.items || []);
      } catch {
        console.error('Failed to load categories/suppliers metadata');
      }
    };
    fetchMetadata();
  }, []);

  const handleOpenAdd = () => {
    setEditProduct(null);
    setSku('');
    setName('');
    setDescription('');
    setCatId(categories[0]?.id || '');
    setSupId(suppliers[0]?.id || '');
    setPrice('');
    setCost('');
    setStock('');
    setMinStock('10');
    setMaxStock('100');
    setReorderPt('20');
    setReorderQty('30');
    setLeadTime('5');
    setModalOpen(true);
  };

  const handleOpenEdit = (product) => {
    setEditProduct(product);
    setSku(product.sku);
    setName(product.name);
    setDescription(product.description || '');
    setCatId(product.category_id || '');
    setSupId(product.supplier_id || '');
    setPrice(product.unit_price.toString());
    setCost(product.cost_price.toString());
    setStock(product.current_stock.toString());
    setMinStock(product.minimum_stock.toString());
    setMaxStock(product.maximum_stock.toString());
    setReorderPt(product.reorder_point.toString());
    setReorderQty(product.reorder_quantity.toString());
    setLeadTime(product.lead_time_days.toString());
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!sku || !name || !price || !cost || !stock) {
      addNotification('Please enter all required fields', 'error');
      return;
    }

    const payload = {
      sku,
      name,
      description,
      category_id: parseInt(catId),
      supplier_id: parseInt(supId),
      unit_price: parseFloat(price),
      cost_price: parseFloat(cost),
      current_stock: parseInt(stock),
      minimum_stock: parseInt(minStock),
      maximum_stock: parseInt(maxStock),
      reorder_point: parseInt(reorderPt),
      reorder_quantity: parseInt(reorderQty),
      lead_time_days: parseInt(leadTime),
    };

    setSaving(true);
    try {
      if (editProduct) {
        await productsApi.update(editProduct.id, payload);
        addNotification('Product updated successfully!', 'success');
      } else {
        await productsApi.create(payload);
        addNotification('Product registered successfully!', 'success');
      }
      setModalOpen(false);
      fetchProducts();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to save product';
      addNotification(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product? This will remove its inventory association.')) return;
    try {
      await productsApi.delete(id);
      addNotification('Product deleted successfully', 'success');
      fetchProducts();
    } catch {
      addNotification('Failed to delete product', 'error');
    }
  };

  return (
    <div className="products-page">
      {/* Search and Action Bar */}
      <div className="card-section" style={{ marginBottom: '24px' }}>
        <div className="section-header">
          <span className="section-title">SKU Product Catalog</span>
          {isManager && (
            <button onClick={handleOpenAdd} className="btn btn-primary">
              + Register New Product
            </button>
          )}
        </div>
        <div className="filter-bar">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search products by SKU or name..."
              className="search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="select-input"
            value={selectedCatId}
            onChange={(e) => setSelectedCatId(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Catalog Table */}
      <div className="card-section">
        {loading ? (
          <LoadingSpinner />
        ) : products.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🏷️</span>
            <p className="empty-state-text">No products in catalog yet.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product Name</th>
                  <th>Category</th>
                  <th>Supplier</th>
                  <th style={{ textAlign: 'right' }}>Unit Price</th>
                  <th style={{ textAlign: 'right' }}>Cost Price</th>
                  <th style={{ textAlign: 'right' }}>Lead Time</th>
                  <th style={{ textAlign: 'right' }}>Reorder Qty</th>
                  {isManager && <th>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: '13px' }}>{p.sku}</td>
                    <td>
                      <div style={{ fontWeight: '600' }}>{p.name}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {p.description}
                      </div>
                    </td>
                    <td>{p.category?.name}</td>
                    <td>{p.supplier?.name}</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(p.unit_price)}</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(p.cost_price)}</td>
                    <td style={{ textAlign: 'right' }}>{p.lead_time_days} days</td>
                    <td style={{ textAlign: 'right' }}>{formatNumber(p.reorder_quantity)}</td>
                    {isManager && (
                      <td>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleOpenEdit(p)}
                            className="btn btn-secondary"
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                          >
                            Edit
                          </button>
                          {isAdmin && (
                            <button
                              onClick={() => handleDelete(p.id)}
                              className="btn btn-danger"
                              style={{ padding: '6px 12px', fontSize: '12px' }}
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Register/Edit Product Modal */}
      {modalOpen && (
        <Modal
          title={editProduct ? `Edit Product: ${editProduct.name}` : 'Register New Product'}
          onClose={() => setModalOpen(false)}
        >
          <form onSubmit={handleSubmit} style={{ maxHeight: '70vh', overflowY: 'auto', paddingRight: '4px' }}>
            <div className="form-group">
              <label>Product SKU Code (Required)</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. ELEC-007"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                disabled={!!editProduct}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Product Name (Required)</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Bluetooth Earbuds"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                className="form-control"
                placeholder="Enter description..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows="2"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Category</label>
                <select
                  className="select-input"
                  style={{ width: '100%' }}
                  value={catId}
                  onChange={(e) => setCatId(e.target.value)}
                  required
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Supplier</label>
                <select
                  className="select-input"
                  style={{ width: '100%' }}
                  value={supId}
                  onChange={(e) => setSupId(e.target.value)}
                  required
                >
                  {suppliers.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label>Selling Price ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="form-control"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Cost Price ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  className="form-control"
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Initial Stock</label>
                <input
                  type="number"
                  min="0"
                  className="form-control"
                  value={stock}
                  onChange={(e) => setStock(e.target.value)}
                  disabled={!!editProduct}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label>Min (Safety) Stock</label>
                <input
                  type="number"
                  min="0"
                  className="form-control"
                  value={minStock}
                  onChange={(e) => setMinStock(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Max Capacity</label>
                <input
                  type="number"
                  min="1"
                  className="form-control"
                  value={maxStock}
                  onChange={(e) => setMaxStock(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Lead Time (Days)</label>
                <input
                  type="number"
                  min="1"
                  className="form-control"
                  value={leadTime}
                  onChange={(e) => setLeadTime(e.target.value)}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label>Reorder Point</label>
                <input
                  type="number"
                  min="0"
                  className="form-control"
                  value={reorderPt}
                  onChange={(e) => setReorderPt(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Reorder Qty</label>
                <input
                  type="number"
                  min="1"
                  className="form-control"
                  value={reorderQty}
                  onChange={(e) => setReorderQty(e.target.value)}
                  required
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setModalOpen(false)}
                disabled={saving}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Product'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
