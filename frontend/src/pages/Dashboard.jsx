import { useEffect, useState, useCallback } from 'react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { dashboardApi, alertsApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { formatCurrency, formatNumber, formatDate } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';

const COLORS = {
  'Healthy': '#10b981',
  'Low Stock': '#f59e0b',
  'Out of Stock': '#ef4444',
  'Overstock': '#8b5cf6',
};

const PIE_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [revenueData, setRevenueData] = useState([]);
  const [inventoryData, setInventoryData] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [reorders, setReorders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addNotification } = useNotification();

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [sumRes, revRes, invRes, catRes, alertRes, reorderRes] = await Promise.all([
        dashboardApi.summary(),
        dashboardApi.revenue({ days: 30 }),
        dashboardApi.inventory(),
        dashboardApi.categoryPerformance(),
        dashboardApi.recentAlerts(),
        dashboardApi.reorderItems(),
      ]);

      setSummary(sumRes.data);
      setRevenueData(revRes.data.data);
      setInventoryData(invRes.data.data);
      setCategoryData(catRes.data.data);
      setAlerts(alertRes.data);
      setReorders(reorderRes.data);
    } catch (err) {
      addNotification('Error loading dashboard data', 'error');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [addNotification]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleResolveAlert = async (id) => {
    try {
      await alertsApi.resolve(id);
      addNotification('Alert resolved successfully', 'success');
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch {
      addNotification('Failed to resolve alert', 'error');
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="dashboard-page">
      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">💰</span>
            <span className="kpi-label">Total Revenue</span>
          </div>
          <div className="kpi-value">{formatCurrency(summary?.total_revenue)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">📈</span>
            <span className="kpi-label">Total Sales</span>
          </div>
          <div className="kpi-value">{formatNumber(summary?.total_sales)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">📦</span>
            <span className="kpi-label">Inventory Value</span>
          </div>
          <div className="kpi-value">{formatCurrency(summary?.inventory_value)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🚨</span>
            <span className="kpi-label">Low Stock SKUs</span>
          </div>
          <div className="kpi-value" style={{ color: summary?.low_stock_items > 0 ? '#f59e0b' : 'inherit' }}>
            {summary?.low_stock_items}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">❌</span>
            <span className="kpi-label">Out of Stock</span>
          </div>
          <div className="kpi-value" style={{ color: summary?.out_of_stock_items > 0 ? '#ef4444' : 'inherit' }}>
            {summary?.out_of_stock_items}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🔮</span>
            <span className="kpi-label">7-Day Forecast Demand</span>
          </div>
          <div className="kpi-value">{formatNumber(summary?.forecasted_demand)}</div>
        </div>
      </div>

      {/* Charts section */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Sales Trend (Last 30 Days)</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)"/>
                <XAxis dataKey="label" tickFormatter={(v) => v.substring(5)} stroke="var(--text-muted)"/>
                <YAxis stroke="var(--text-muted)" tickFormatter={(v) => `$${v}`}/>
                <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue']}/>
                <Area type="monotone" dataKey="value" stroke="#6366f1" fillOpacity={1} fill="url(#colorRev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Inventory Health Distribution</span>
          </div>
          <div className="chart-wrapper" style={{ display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={inventoryData.filter(d => d.value > 0)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {inventoryData.filter(d => d.value > 0).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.label] || PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card" style={{ gridColumn: 'span 2' }}>
          <div className="chart-card-header">
            <span className="chart-card-title">Category Revenue Performance</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)"/>
                <XAxis dataKey="label" stroke="var(--text-muted)"/>
                <YAxis stroke="var(--text-muted)" tickFormatter={(v) => `$${v}`}/>
                <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue']}/>
                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#6366f1' : '#8b5cf6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom panels: Reorders and Alerts */}
      <div className="charts-grid">
        {/* Recommended Reorders */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Recommended Action Reorders</span>
          </div>
          <div className="table-responsive" style={{ flex: 1 }}>
            {reorders.length === 0 ? (
              <div className="empty-state" style={{ height: '100%' }}>
                <span>🎉 All product stock levels are stable!</span>
              </div>
            ) : (
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Recommended Qty</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {reorders.map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontWeight: '500' }}>{r.product_name}</td>
                      <td>{r.recommended_quantity} units</td>
                      <td>
                        <span className={`badge badge-${r.risk_level === 'high' || r.risk_level === 'critical' ? 'danger' : r.risk_level === 'medium' ? 'warning' : 'success'}`}>
                          {r.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Recent Intelligence Alerts</span>
          </div>
          <div className="table-responsive" style={{ flex: 1 }}>
            {alerts.length === 0 ? (
              <div className="empty-state" style={{ height: '100%' }}>
                <span>🔔 No pending active alerts.</span>
              </div>
            ) : (
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Alert Message</th>
                    <th>Severity</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((a) => (
                    <tr key={a.id}>
                      <td style={{ fontSize: '13px', lineHeight: '1.4' }}>{a.message}</td>
                      <td>
                        <span className={`badge badge-${a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info'}`}>
                          {a.severity}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => handleResolveAlert(a.id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '12px' }}
                        >
                          Resolve
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
