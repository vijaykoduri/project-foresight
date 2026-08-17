export const formatCurrency = (value) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);

export const formatNumber = (value) =>
  new Intl.NumberFormat('en-US').format(value || 0);

export const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
};

export const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
};

export const stockStatusLabel = (status) => {
  const labels = {
    healthy: 'Healthy',
    low_stock: 'Low Stock',
    out_of_stock: 'Out of Stock',
    overstock: 'Overstock',
  };
  return labels[status] || status;
};

export const stockStatusClass = (status) => {
  const classes = {
    healthy: 'badge-success',
    low_stock: 'badge-warning',
    out_of_stock: 'badge-danger',
    overstock: 'badge-info',
  };
  return classes[status] || 'badge-default';
};

export const riskClass = (level) => {
  const classes = {
    low: 'badge-success',
    medium: 'badge-warning',
    high: 'badge-danger',
    critical: 'badge-critical',
  };
  return classes[level] || 'badge-default';
};

export const severityClass = (severity) => {
  const classes = {
    info: 'badge-info',
    warning: 'badge-warning',
    critical: 'badge-critical',
  };
  return classes[severity] || 'badge-default';
};
