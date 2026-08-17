import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useNotification } from '../context/NotificationContext';
import { authApi } from '../services/api';

export default function Settings() {
  const { user, updateUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { addNotification } = useNotification();

  // Profile Form state
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [updatingProfile, setUpdatingProfile] = useState(false);

  // Password Form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [updatingPassword, setUpdatingPassword] = useState(false);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    if (!fullName || !email) {
      addNotification('Name and email are required', 'error');
      return;
    }

    setUpdatingProfile(true);
    try {
      const res = await authApi.updateMe({ full_name: fullName, email });
      updateUser(res.data);
      addNotification('Profile updated successfully!', 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update profile';
      addNotification(msg, 'error');
    } finally {
      setUpdatingProfile(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      addNotification('All password fields are required', 'error');
      return;
    }
    if (newPassword !== confirmPassword) {
      addNotification('New passwords do not match', 'error');
      return;
    }

    setUpdatingPassword(true);
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      addNotification('Password updated successfully!', 'success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update password';
      addNotification(msg, 'error');
    } finally {
      setUpdatingPassword(false);
    }
  };

  return (
    <div className="settings-page">
      <div className="charts-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        {/* User profile details */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">User Account Profile</span>
          </div>
          <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div className="form-group">
              <label htmlFor="settingsName">Full Name</label>
              <input
                type="text"
                id="settingsName"
                className="form-control"
                placeholder="User name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="settingsEmail">Email Address</label>
              <input
                type="email"
                id="settingsEmail"
                className="form-control"
                placeholder="email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div style={{ marginTop: 'auto', paddingTop: '16px' }}>
              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={updatingProfile}
              >
                {updatingProfile ? 'Saving Changes...' : 'Update Account Profile'}
              </button>
            </div>
          </form>
        </div>

        {/* Change password */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Change Password</span>
          </div>
          <form onSubmit={handleUpdatePassword}>
            <div className="form-group">
              <label htmlFor="currPass">Current Password</label>
              <input
                type="password"
                id="currPass"
                className="form-control"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="newPass">New Password</label>
              <input
                type="password"
                id="newPass"
                className="form-control"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="confPass">Confirm New Password</label>
              <input
                type="password"
                id="confPass"
                className="form-control"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <div style={{ marginTop: '16px' }}>
              <button
                type="submit"
                className="btn btn-secondary"
                style={{ width: '100%' }}
                disabled={updatingPassword}
              >
                {updatingPassword ? 'Updating Password...' : 'Save New Password'}
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="charts-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))' }}>
        {/* Global theme controls */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Aesthetics & Layout Settings</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', justifyContent: 'center', height: '100%', paddingBottom: '24px' }}>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              Foresight supports dark mode layouts to prevent eye strain and save battery life. Switch between themes seamlessly:
            </p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: '600' }}>Active Color Mode</span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={toggleTheme}
                style={{ minWidth: '130px', textTransform: 'capitalize' }}
              >
                {theme === 'light' ? '☀️ Light Mode' : '🌙 Dark Mode'}
              </button>
            </div>
          </div>
        </div>

        {/* System parameters details */}
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-title">Foresight System Information</span>
          </div>
          <div style={{ fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>App Name</span>
              <span style={{ fontWeight: '600' }}>Foresight Intelligence</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Environment</span>
              <span style={{ fontWeight: '600', textTransform: 'uppercase' }}>Development</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Local Engine Port</span>
              <span style={{ fontWeight: '600', fontFamily: 'var(--mono)' }}>8000 (API)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Dialect Engine</span>
              <span style={{ fontWeight: '600', textTransform: 'uppercase' }}>SQLite / SQLAlchemy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
