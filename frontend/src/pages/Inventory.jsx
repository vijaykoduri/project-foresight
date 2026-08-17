import { useEffect, useState } from 'react';
import { inventoryApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { formatCurrency, formatNumber, stockStatusLabel, stockStatusClass } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Modal from '../components/common/Modal';

export default function Inventory() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [categories, setCategories] = useState([]);
  
  // Sorting state
  const [sortField, setSortField] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  // Modal adjustment state
  const [adjustModalOpen, setAdjustModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [qtyChange, setQtyChange] = useState('');
  const [txType, setTxType] = useState('incoming');
  const [notes, setNotes] = useState('');
  const [reference, setReference] = useState('');
  const [adjusting, setAdjusting] = useState(false);

  const { addNotification } = useNotification();

  const fetchInventory = async () => {
    try {
      setLoading(true);
      const res = await inventoryApi.summary();
      setData(res.data);
      
      // Extract unique categories for filter
      const uniqueCats = [...new Set(res.data.items.map(item => item.category_name))].filter(Boolean);
      setCategories(uniqueCats);
    } catch {
      addNotification('Error loading inventory data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const handleOpenAdjust = (product) => {
    setSelectedProduct(product);
    setQtyChange('');
    setTxType('incoming');
    setReference('');
    setNotes('');
    setAdjustModalOpen(true);
  };

  const handleAdjustSubmit = async (e) => {
    e.preventDefault();
    if (!qtyChange || isNaN(qtyChange)) {
      addNotification('Please enter a valid quantity', 'error');
      return;
    }

    const changeNum = parseInt(qtyChange);
    if (changeNum <= 0) {
      addNotification('Quantity must be greater than zero', 'error');
      return;
    }

    // Outgoing transaction should be negative
    const finalChange = txType === 'outgoing' ? -changeNum : changeNum;

    setAdjusting(true);
    try {
      await inventoryApi.adjust({
        product_id: selectedProduct.product_id,
        quantity_change: finalChange,
        transaction_type: txType,
        reference: reference || 'MANUAL-ADJUST',
        notes: notes || 'Manual adjustment from inventory screen'
      });
      addNotification('Stock level adjusted successfully', 'success');
      setAdjustModalOpen(false);
      fetchInventory(); // Reload
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to adjust stock';
      addNotification(msg, 'error');
    } finally {
      setAdjusting(false);
    }
  };

  const handleSort = (field) => {
    const isAsc = sortField === field && sortOrder === 'asc';
    setSortField(field);
    setSortOrder(isAsc ? 'desc' : 'asc');
  };

  if (loading) return <LoadingSpinner />;

  // Filter items
  const filteredItems = (data?.items || []).filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase()) ||
                          item.sku.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || item.stock_status === statusFilter;
    const matchesCategory = !categoryFilter || item.category_name === categoryFilter;
    return matchesSearch && matchesStatus && matchesCategory;
  });

  // Sort items
  const sortedItems = [...filteredItems].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];

    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="inventory-page">
      {/* Top statistics summary panel */}
      <div className="kpi-grid" style={{ marginBottom: '24px' }}>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">📦</span>
            <span className="kpi-label">Total Inventory Value</span>
          </div>
          <div className="kpi-value">{formatCurrency(data?.total_inventory_value)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🏷️</span>
            <span className="kpi-label">Total SKUs</span>
          </div>
          <div className="kpi-value">{formatNumber(data?.total_products)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🟢</span>
            <span className="kpi-label">Healthy Stock</span>
          </div>
          <div className="kpi-value">{formatNumber(data?.healthy_stock_count)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🟡</span>
            <span className="kpi-label">Low Stock</span>
          </div>
          <div className="kpi-value">{formatNumber(data?.low_stock_count)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🔴</span>
            <span className="kpi-label">Out of Stock</span>
          </div>
          <div className="kpi-value">{formatNumber(data?.out_of_stock_count)}</div>
        </div>
      </div>

      {/* Filter and Search controls */}
      <div className="card-section">
        <div className="filter-bar">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search by SKU or name..."
              className="search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="select-input"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <select
            className="select-input"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Stock Statuses</option>
            <option value="healthy">Healthy</option>
            <option value="low_stock">Low Stock</option>
            <option value="out_of_stock">Out of Stock</option>
            <option value="overstock">Overstock</option>
          </select>
        </div>

        {/* Stock list table */}
        <div className="table-responsive">
          {sortedItems.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state-icon">📂</span>
              <p className="empty-state-text">No products match the search or filter criteria.</p>
            </div>
          ) : (
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('sku')}>
                    SKU {sortField === 'sku' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </th>
                  <th style={{ cursor: 'pointer' }} onClick={() => handleSort('name')}>
                    Product Name {sortField === 'name' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </th>
                  <th>Category</th>
                  <th style={{ cursor: 'pointer', textAlign: 'right' }} onClick={() => handleSort('current_stock')}>
                    Stock {sortField === 'current_stock' ? (sortOrder === 'asc' ? '▲' : '▼') : ''}
                  </th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Reorder Point</th>
                  <th style={{ textAlign: 'right' }}>Safety Stock</th>
                  <th style={{ textAlign: 'right' }}>Unit Cost</th>
                  <th style={{ textAlign: 'right' }}>Value</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedItems.map((item) => (
                  <tr key={item.product_id}>
                    <td style={{ fontFamily: 'var(--mono)', fontSize: '13px' }}>{item.sku}</td>
                    <td style={{ fontWeight: '600' }}>{item.name}</td>
                    <td>{item.category_name}</td>
                    <td style={{ textAlign: 'right', fontWeight: '500' }}>
                      {formatNumber(item.current_stock)}
                    </td>
                    <td>
                      <span className={`badge ${stockStatusClass(item.stock_status)}`}>
                        {stockStatusLabel(item.stock_status)}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>{formatNumber(item.reorder_point)}</td>
                    <td style={{ textAlign: 'right' }}>{formatNumber(item.minimum_stock)}</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(item.cost_price)}</td>
                    <td style={{ textAlign: 'right', fontWeight: '500' }}>{formatCurrency(item.inventory_value)}</td>
                    <td>
                      <button
                        onClick={() => handleOpenAdjust(item)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        Adjust Stock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Adjust Stock Modal */}
      {adjustModalOpen && selectedProduct && (
        <Modal
          title={`Adjust Stock: ${selectedProduct.name}`}
          onClose={() => setAdjustModalOpen(false)}
        >
          <form onSubmit={handleAdjustSubmit}>
            <div style={{ marginBottom: '16px', fontSize: '14px', color: 'var(--text-secondary)' }}>
              Current stock level: <strong>{selectedProduct.current_stock} units</strong>
            </div>
            
            <div className="form-group">
              <label>Transaction Type</label>
              <select
                className="select-input"
                style={{ width: '100%' }}
                value={txType}
                onChange={(e) => setTxType(e.target.value)}
              >
                <option value="incoming">Incoming / Stock replenishment</option>
                <option value="outgoing">Outgoing / Stock dispatch</option>
                <option value="adjustment">Audit / Discrepancy Adjustment</option>
              </select>
            </div>

            <div className="form-group">
              <label>Quantity to Change</label>
              <input
                type="number"
                min="1"
                className="form-control"
                placeholder="Enter units quantity"
                value={qtyChange}
                onChange={(e) => setQtyChange(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Reference Code / PO</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. PO-10293 or AUDIT-2026"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Reason / Notes</label>
              <textarea
                className="form-control"
                placeholder="Describe why stock is being modified..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows="3"
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '24px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setAdjustModalOpen(false)}
                disabled={adjusting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={adjusting}
              >
                {adjusting ? 'Adjusting...' : 'Save Adjustments'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
