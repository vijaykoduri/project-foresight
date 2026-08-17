import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotification } from '../context/NotificationContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { addNotification } = useNotification();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      addNotification('Please enter both email and password', 'error');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      addNotification('Logged in successfully!', 'success');
      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password';
      addNotification(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUseDemo = (demoEmail, demoPassword) => {
    setEmail(demoEmail);
    setPassword(demoPassword);
    addNotification('Autofilled demo credentials!', 'success');
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">F</div>
          <h2 className="auth-title">Welcome Back</h2>
          <p className="auth-subtitle">Sign in to Foresight Demand Intelligence</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              className="form-control"
              placeholder="admin@foresight.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary auth-btn"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="auth-footer">
          Don't have an account? <Link to="/register">Register here</Link>
        </div>
        
        <div className="demo-accounts-section">
          <h3 className="demo-accounts-title">DEMO ACCOUNTS</h3>
          <div className="demo-accounts-list">
            <div className="demo-account-item">
              <div className="demo-account-info">
                <span className="demo-account-role">Administrator</span>
                <span className="demo-account-email">admin@foresight.local</span>
              </div>
              <button
                type="button"
                className="demo-account-use-btn"
                onClick={() => handleUseDemo('admin@foresight.local', 'Admin@12345')}
              >
                Use →
              </button>
            </div>
            <div className="demo-account-item">
              <div className="demo-account-info">
                <span className="demo-account-role">Manager</span>
                <span className="demo-account-email">manager@foresight.local</span>
              </div>
              <button
                type="button"
                className="demo-account-use-btn"
                onClick={() => handleUseDemo('manager@foresight.local', 'Manager@12345')}
              >
                Use →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
