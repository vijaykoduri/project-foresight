import { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);

  const addNotification = useCallback((message, type = 'success') => {
    const id = Date.now();
    
    let formattedMessage = '';
    try {
      if (message && typeof message === 'object') {
        if (Array.isArray(message)) {
          formattedMessage = message.map(err => {
            if (err && typeof err === 'object') {
              const field = err.loc ? err.loc[err.loc.length - 1] : '';
              const fieldStr = field ? `"${field}" ` : '';
              return `${fieldStr}${err.msg || JSON.stringify(err)}`;
            }
            return String(err);
          }).join(', ');
        } else if (message.detail) {
          const detail = message.detail;
          if (typeof detail === 'string') {
            formattedMessage = detail;
          } else if (Array.isArray(detail)) {
            formattedMessage = detail.map(err => {
              if (err && typeof err === 'object') {
                const field = err.loc ? err.loc[err.loc.length - 1] : '';
                const fieldStr = field ? `"${field}" ` : '';
                return `${fieldStr}${err.msg || JSON.stringify(err)}`;
              }
              return String(err);
            }).join(', ');
          } else {
            formattedMessage = JSON.stringify(detail);
          }
        } else {
          formattedMessage = JSON.stringify(message);
        }
      } else {
        formattedMessage = String(message || 'An error occurred');
      }
    } catch (e) {
      formattedMessage = 'An unexpected error occurred';
    }

    setNotifications((prev) => [...prev, { id, message: formattedMessage, type }]);
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, 4000);
  }, []);

  const removeNotification = (id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <NotificationContext.Provider value={{ addNotification }}>
      {children}
      <div className="notification-container">
        {notifications.map((n) => (
          <div key={n.id} className={`notification notification-${n.type}`} onClick={() => removeNotification(n.id)}>
            {n.message}
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

export const useNotification = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error('useNotification must be used within NotificationProvider');
  return ctx;
};
