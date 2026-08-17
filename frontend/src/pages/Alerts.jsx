import { useEffect, useState, useCallback } from 'react';
import { alertsApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { formatDateTime, severityClass } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [severityFilter, setSeverityFilter] = useState('');
  const [resolvedFilter, setResolvedFilter] = useState('false'); // Default to unresolved
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const { addNotification } = useNotification();

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (severityFilter) params.severity = severityFilter;
      if (resolvedFilter !== '') params.is_resolved = resolvedFilter === 'true';
      
      const res = await alertsApi.list(params);
      setAlerts(res.data.items || []);
    } catch {
      addNotification('Error loading alerts list', 'error');
    } finally {
      setLoading(false);
    }
  }, [severityFilter, resolvedFilter, addNotification]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleResolve = async (id) => {
    try {
      await alertsApi.resolve(id);
      addNotification('Alert marked as resolved', 'success');
      fetchAlerts(); // Reload list
    } catch {
      addNotification('Failed to resolve alert', 'error');
    }
  };

  const handleTriggerGenerate = async () => {
    setGenerating(true);
    try {
      const res = await alertsApi.generate();
      addNotification(res.data.message || 'Alert generation complete!', 'success');
      fetchAlerts();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate alerts';
      addNotification(msg, 'error');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="alerts-page">
      {/* Configuration Header Controls */}
      <div className="card-section" style={{ marginBottom: '24px' }}>
        <div className="section-header">
          <span className="section-title">Demand & Stockout Risk Warnings</span>
          <button
            onClick={handleTriggerGenerate}
            className="btn btn-primary"
            disabled={generating}
          >
            {generating ? 'Scanning Inventory...' : 'Scan & Re-Evaluate Alerts'}
          </button>
        </div>
        
        <div className="filter-bar">
          <select
            className="select-input"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <select
            className="select-input"
            value={resolvedFilter}
            onChange={(e) => setResolvedFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="false">Active Warnings (Unresolved)</option>
            <option value="true">Resolved Archives</option>
          </select>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="card-section">
        {loading ? (
          <LoadingSpinner />
        ) : alerts.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon">🔔</span>
            <p className="empty-state-text">No alerts matching the selected filters found.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Product</th>
                  <th>Alert Details</th>
                  <th>Category</th>
                  <th>Triggered At</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <span className={`badge ${severityClass(a.severity)}`}>
                        {a.severity}
                      </span>
                    </td>
                    <td style={{ fontWeight: '600' }}>
                      {a.product_name || 'System'}
                    </td>
                    <td>{a.message}</td>
                    <td style={{ textTransform: 'capitalize' }}>
                      {a.alert_type.replace('_', ' ')}
                    </td>
                    <td>{formatDateTime(a.created_at)}</td>
                    <td>
                      {a.is_resolved ? (
                        <span className="badge badge-success">Resolved</span>
                      ) : (
                        <span className="badge badge-warning">Active</span>
                      )}
                    </td>
                    <td>
                      {!a.is_resolved ? (
                        <button
                          onClick={() => handleResolve(a.id)}
                          className="btn btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                        >
                          Mark Resolved
                        </button>
                      ) : (
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          Closed at {a.resolved_at ? formatDateTime(a.resolved_at).split(',')[0] : '-'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
