import { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { analyticsApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { formatCurrency, formatNumber } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const { addNotification } = useNotification();

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const [sumRes, trendRes] = await Promise.all([
        analyticsApi.summary({ days }),
        analyticsApi.trends({ days })
      ]);
      setSummary(sumRes.data);
      setTrends(trendRes.data);
    } catch {
      addNotification('Error loading analytics data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [days]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="analytics-page">
      {/* Time Range Selector */}
      <div className="card-section" style={{ marginBottom: '24px' }}>
        <div className="section-header" style={{ margin: 0 }}>
          <span className="section-title">Performance Analytics</span>
          <select
            className="select-input"
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
          >
            <option value="7">Last 7 Days</option>
            <option value="14">Last 14 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* Analytics KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">📊</span>
            <span className="kpi-label">Sales Volume Growth</span>
          </div>
          <div className="kpi-value" style={{ color: (summary?.sales_growth || 0) >= 0 ? '#10b981' : '#ef4444' }}>
            {(summary?.sales_growth || 0) >= 0 ? '+' : ''}{summary?.sales_growth}%
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">💸</span>
            <span className="kpi-label">Revenue Growth</span>
          </div>
          <div className="kpi-value" style={{ color: (summary?.revenue_growth || 0) >= 0 ? '#10b981' : '#ef4444' }}>
            {(summary?.revenue_growth || 0) >= 0 ? '+' : ''}{summary?.revenue_growth}%
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🔄</span>
            <span className="kpi-label">Inventory Turnover</span>
          </div>
          <div className="kpi-value">{summary?.inventory_turnover}x</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">⚠️</span>
            <span className="kpi-label">Stockout Frequency</span>
          </div>
          <div className="kpi-value" style={{ color: (summary?.stockout_frequency || 0) > 5 ? '#ef4444' : 'inherit' }}>
            {summary?.stockout_frequency}%
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-icon">🧾</span>
            <span className="kpi-label">Avg Order Value</span>
          </div>
          <div className="kpi-value">{formatCurrency(summary?.avg_order_value)}</div>
        </div>
      </div>

      {/* Historical Demand & Revenue Timeline */}
      <div className="charts-grid">
        <div className="chart-card" style={{ gridColumn: 'span 2' }}>
          <div className="chart-card-header">
            <span className="chart-card-title">Daily Sales & Units Volume Timeline</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends?.revenue_trend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)"/>
                <XAxis dataKey="label" tickFormatter={(v) => v.substring(5)} stroke="var(--text-muted)"/>
                <YAxis stroke="var(--text-muted)" tickFormatter={(v) => `$${v}`}/>
                <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue']}/>
                <Legend />
                <Line type="monotone" name="Revenue ($)" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Product performance grids: Top selling vs slow moving */}
      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Top 10 Selling Products (Units)</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends?.top_products} layout="vertical" margin={{ left: 50, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-color)"/>
                <XAxis type="number" stroke="var(--text-muted)"/>
                <YAxis type="category" dataKey="label" stroke="var(--text-muted)" width={100} style={{ fontSize: '11px' }}/>
                <Tooltip formatter={(value) => [formatNumber(value), 'Units Sold']}/>
                <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Slow-Moving Products (Units)</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends?.low_performing_products} layout="vertical" margin={{ left: 50, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border-color)"/>
                <XAxis type="number" stroke="var(--text-muted)"/>
                <YAxis type="category" dataKey="label" stroke="var(--text-muted)" width={100} style={{ fontSize: '11px' }}/>
                <Tooltip formatter={(value) => [formatNumber(value), 'Units Sold']}/>
                <Bar dataKey="value" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Supplier Performance breakdown */}
      <div className="charts-grid">
        <div className="chart-card" style={{ gridColumn: 'span 2' }}>
          <div className="chart-card-header">
            <span className="chart-card-title">Supplier Performance (Revenue Share)</span>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={trends?.supplier_performance}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)"/>
                <XAxis dataKey="label" stroke="var(--text-muted)"/>
                <YAxis stroke="var(--text-muted)" tickFormatter={(v) => `$${v}`}/>
                <Tooltip formatter={(value) => [formatCurrency(value), 'Revenue Generated']}/>
                <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                  {trends?.supplier_performance.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366f1' : '#8b5cf6'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
