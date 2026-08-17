import { formatCurrency, formatNumber } from '../../utils/format';

export default function KPICard({ label, value, format = 'number', icon }) {
  const display = format === 'currency' ? formatCurrency(value)
    : format === 'number' ? formatNumber(value)
    : value;

  return (
    <div className="kpi-card">
      <div className="kpi-card-header">
        {icon && <span className="kpi-icon">{icon}</span>}
        <span className="kpi-label">{label}</span>
      </div>
      <div className="kpi-value">{display}</div>
    </div>
  );
}
