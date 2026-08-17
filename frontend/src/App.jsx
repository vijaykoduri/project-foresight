import { Routes, Route, Navigate, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';
import LoadingSpinner from './components/common/LoadingSpinner';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Forecast from './pages/Forecast';
import Analytics from './pages/Analytics';
import Alerts from './pages/Alerts';
import Products from './pages/Products';
import Settings from './pages/Settings';

// Route Guard for Protected Pages
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

// Sidebar & Main Layout Wrapper
function Layout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Executive Summary Dashboard';
      case '/inventory': return 'Inventory & Replenishment Control';
      case '/forecast': return 'AI Predictive Demand Forecasting';
      case '/analytics': return 'Efficiency & Analytics Panel';
      case '/alerts': return 'Intelligence Risk Alerts';
      case '/products': return 'SKU Product Catalog';
      case '/settings': return 'System Settings';
      default: return 'Foresight Intelligence';
    }
  };

  return (
    <div className="app-container" data-theme={theme}>
      {/* Navigation Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">F</div>
          <span className="sidebar-title">FORESIGHT</span>
        </div>
        <ul className="sidebar-menu">
          <li className={`sidebar-item ${location.pathname === '/' ? 'active' : ''}`}>
            <Link to="/">
              <span>📊</span> Executive Dashboard
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/inventory' ? 'active' : ''}`}>
            <Link to="/inventory">
              <span>📦</span> Inventory Control
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/forecast' ? 'active' : ''}`}>
            <Link to="/forecast">
              <span>🔮</span> Demand Forecast
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/analytics' ? 'active' : ''}`}>
            <Link to="/analytics">
              <span>📈</span> Analytics Metrics
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/alerts' ? 'active' : ''}`}>
            <Link to="/alerts">
              <span>🚨</span> Alerts & Warnings
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/products' ? 'active' : ''}`}>
            <Link to="/products">
              <span>🏷️</span> Product Catalog
            </Link>
          </li>
          <li className={`sidebar-item ${location.pathname === '/settings' ? 'active' : ''}`}>
            <Link to="/settings">
              <span>⚙️</span> System Settings
            </Link>
          </li>
        </ul>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="logout-btn">
            <span>🚪</span> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Container */}
      <main className="main-content">
        {/* Top Header */}
        <header className="app-header">
          <div className="header-title">
            <h2>{getPageTitle()}</h2>
          </div>
          <div className="header-actions">
            <button onClick={toggleTheme} className="theme-toggle" title="Toggle theme">
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <div className="user-profile">
              <div className="user-avatar">
                {user?.full_name ? user.full_name.substring(0, 1).toUpperCase() : 'U'}
              </div>
              <div className="user-info">
                <span className="user-name">{user?.full_name || 'Foresight User'}</span>
                <span className="user-role">{user?.role?.name || 'Staff'}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Page Views */}
        <div className="page-container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/products" element={<Products />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Public Pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Pages under Main Layout */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
