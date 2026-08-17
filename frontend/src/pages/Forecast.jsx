import { useEffect, useState, useCallback } from 'react';
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { productsApi, forecastApi } from '../services/api';
import { useNotification } from '../context/NotificationContext';
import { formatNumber, formatDate } from '../utils/format';
import LoadingSpinner from '../components/common/LoadingSpinner';

export default function Forecast() {
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [horizon, setHorizon] = useState(30);
  const [forecast, setForecast] = useState(null);
  
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [generating, setGenerating] = useState(false);
  const { addNotification } = useNotification();

  // Load active products list
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoadingProducts(true);
        const res = await productsApi.list({ limit: 100 });
        setProducts(res.data.items || []);
        if (res.data.items?.length > 0) {
          setSelectedProductId(res.data.items[0].id);
        }
      } catch {
        addNotification('Error loading products list', 'error');
      } finally {
        setLoadingProducts(false);
      }
    };
    fetchProducts();
  }, [addNotification]);

  const loadLatestForecast = useCallback(async (productId) => {
    if (!productId) return;
    try {
      const res = await forecastApi.get(productId);
      if (res.data) {
        setForecast(res.data);
      } else {
        setForecast(null);
      }
    } catch {
      // It's okay if no forecast is generated yet
      setForecast(null);
    }
  }, []);

  useEffect(() => {
    if (selectedProductId) {
      loadLatestForecast(selectedProductId);
    }
  }, [selectedProductId, loadLatestForecast]);

  const handleGenerateForecast = async (e) => {
    e.preventDefault();
    if (!selectedProductId) {
      addNotification('Please select a product first', 'error');
      return;
    }

    setGenerating(true);
    try {
      const res = await forecastApi.generate({
        product_id: parseInt(selectedProductId),
        horizon_days: parseInt(horizon)
      });
      setForecast(res.data);
      addNotification('AI demand forecast generated successfully!', 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to generate forecast';
      addNotification(msg, 'error');
    } finally {
      setGenerating(false);
    }
  };

  if (loadingProducts) return <LoadingSpinner />;

  // Prepare chart data: split results into historical vs forecast
  const chartData = (forecast?.results || []).map((r) => ({
    date: formatDate(r.forecast_date),
    historical: r.is_historical ? r.predicted_demand : null,
    predicted: !r.is_historical ? r.predicted_demand : null,
    bounds: !r.is_historical ? [r.lower_bound, r.upper_bound] : null,
    lower: r.lower_bound,
    upper: r.upper_bound,
    rawDate: r.forecast_date
  }));

  // Identify where the transition line should be drawn
  const lastHistorical = chartData.filter(d => d.historical !== null).pop();
  const transitionDate = lastHistorical ? lastHistorical.date : null;

  return (
    <div className="forecast-page">
      {/* Configuration Header Controls */}
      <div className="card-section">
        <span className="section-title" style={{ display: 'block', marginBottom: '20px' }}>
          AI Demand Forecasting Model
        </span>
        <form onSubmit={handleGenerateForecast} className="filter-bar" style={{ alignItems: 'flex-end' }}>
          <div className="form-group" style={{ flex: 1, minWidth: '220px', marginBottom: 0 }}>
            <label htmlFor="productSelect">Select SKU Product</label>
            <select
              id="productSelect"
              className="select-input"
              style={{ width: '100%' }}
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.sku} - {p.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group" style={{ minWidth: '150px', marginBottom: 0 }}>
            <label htmlFor="horizonSelect">Forecast Horizon</label>
            <select
              id="horizonSelect"
              className="select-input"
              style={{ width: '100%' }}
              value={horizon}
              onChange={(e) => setHorizon(e.target.value)}
            >
              <option value="7">Next 7 Days</option>
              <option value="14">Next 14 Days</option>
              <option value="30">Next 30 Days</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ height: '44px', padding: '0 24px' }}
            disabled={generating}
          >
            {generating ? 'Calculating Forecast...' : 'Generate AI Forecast'}
          </button>
        </form>
      </div>

      {forecast ? (
        <>
          {/* Model Statistics Panel */}
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-icon">🧠</span>
                <span className="kpi-label">Algorithm Used</span>
              </div>
              <div className="kpi-value" style={{ fontSize: '18px', textTransform: 'uppercase' }}>
                {forecast.model_type.replace('_', ' ')}
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-icon">🎯</span>
                <span className="kpi-label">Confidence Score</span>
              </div>
              <div className="kpi-value">
                {(forecast.confidence_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-icon">📏</span>
                <span className="kpi-label">MAE (Error Rate)</span>
              </div>
              <div className="kpi-value">
                {forecast.mae !== null ? forecast.mae.toFixed(2) : 'N/A'}
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-icon">📐</span>
                <span className="kpi-label">RMSE</span>
              </div>
              <div className="kpi-value">
                {forecast.rmse !== null ? forecast.rmse.toFixed(2) : 'N/A'}
              </div>
            </div>
          </div>

          {/* Forecasting Visualization Chart */}
          <div className="card-section">
            <div className="section-header">
              <span className="section-title">Demand Forecast Visualizer (Daily Units)</span>
              <div style={{ fontSize: '13px', display: 'flex', gap: '16px', color: 'var(--text-secondary)' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ display: 'inline-block', width: '12px', height: '4px', backgroundColor: '#94a3b8' }}></span>
                  Historical Demand
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ display: 'inline-block', width: '12px', height: '4px', backgroundColor: '#6366f1' }}></span>
                  Forecasted Demand
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ display: 'inline-block', width: '12px', height: '8px', backgroundColor: 'rgba(99, 102, 241, 0.15)' }}></span>
                  Confidence Interval (Bounds)
                </span>
              </div>
            </div>
            
            <div className="chart-wrapper" style={{ minHeight: '380px', marginTop: '16px' }}>
              <ResponsiveContainer width="100%" height={380}>
                <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)"/>
                  <XAxis dataKey="date" stroke="var(--text-muted)"/>
                  <YAxis stroke="var(--text-muted)"/>
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const data = payload[0].payload;
                      const isHist = data.historical !== null;
                      return (
                        <div className="kpi-card" style={{ padding: '12px 16px', minWidth: '150px' }}>
                          <div style={{ fontWeight: '700', fontSize: '13px', marginBottom: '4px' }}>{data.date}</div>
                          <div style={{ fontSize: '14px' }}>
                            {isHist ? (
                              <span style={{ color: '#94a3b8' }}>Demand: <strong>{data.historical} units</strong></span>
                            ) : (
                              <div>
                                <span style={{ color: '#6366f1' }}>Forecast: <strong>{data.predicted}</strong></span>
                                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                  Range: {data.lower} - {data.upper}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    }}
                  />
                  {transitionDate && (
                    <ReferenceLine x={transitionDate} stroke="#94a3b8" strokeDasharray="5 5" label={{ value: 'Forecast Start', position: 'top', fill: '#64748b', fontSize: 11 }} />
                  )}
                  {/* Confidence Interval Band */}
                  <Area
                    type="monotone"
                    dataKey="bounds"
                    stroke="none"
                    fill="var(--primary)"
                    fillOpacity={0.15}
                  />
                  {/* Historical demand line */}
                  <Line
                    type="monotone"
                    dataKey="historical"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    dot={false}
                  />
                  {/* Predicted demand line */}
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    strokeDasharray="4 4"
                    dot={true}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            
            {forecast.notes && (
              <div style={{ marginTop: '16px', fontSize: '13px', padding: '12px 16px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px', borderLeft: '3px solid var(--warning)' }}>
                ℹ️ <strong>Model Notes:</strong> {forecast.notes}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="card-section empty-state" style={{ padding: '80px 0' }}>
          <span className="empty-state-icon">🔮</span>
          <h2>No Forecast Available</h2>
          <p className="empty-state-text">
            There is no active model prediction generated for this product. Use the button above to run the scikit-learn forecasting machine learning engine.
          </p>
        </div>
      )}
    </div>
  );
}
