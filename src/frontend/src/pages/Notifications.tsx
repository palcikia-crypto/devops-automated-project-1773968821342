import React from 'react';
import { Bell, TrendingUp, TrendingDown, DollarSign, Clock, Check, X, Target, Rocket } from 'lucide-react';

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data?: any;
  read: boolean;
  createdAt: string;
}

interface NotificationsProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
}

const Notifications: React.FC<NotificationsProps> = ({ notifications, onMarkAsRead }) => {
  const markAllAsRead = () => {
    notifications.forEach(notification => {
      if (!notification.read) {
        onMarkAsRead(notification.id);
      }
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'signal':
        return <Target size={20} className="text-cyan-400" />;
      case 'trade':
        return <Rocket size={20} className="text-emerald-400" />;
      case 'alert':
        return <Bell size={20} className="text-amber-400" />;
      case 'error':
        return <X size={20} className="text-red-400" />;
      default:
        return <Bell size={20} className="text-gray-400" />;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'signal':
        return 'bg-cyan-900/30 border-cyan-800';
      case 'trade':
        return 'bg-emerald-900/30 border-emerald-800';
      case 'alert':
        return 'bg-amber-900/30 border-amber-800';
      case 'error':
        return 'bg-red-900/30 border-red-800';
      default:
        return 'bg-gray-900/30 border-gray-800';
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`;
    }
    if (diffInSeconds < 3600) {
      return `${Math.floor(diffInSeconds / 60)}m ago`;
    }
    if (diffInSeconds < 86400) {
      return `${Math.floor(diffInSeconds / 3600)}h ago`;
    }
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Notifications</h1>
        <p className="text-gray-400">View and manage your notifications</p>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="flex gap-4">
          <button
            onClick={markAllAsRead}
            className="btn btn-secondary flex-1 md:flex-none"
          >
            <Check size={18} /> Mark All as Read
          </button>
          <button className="btn btn-secondary flex-1 md:flex-none">
            <X size={18} /> Clear All
          </button>
        </div>
      </div>

      {/* Notification List */}
      <div className="space-y-4">
        {notifications.length === 0 ? (
          <div className="card text-center py-12">
            <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bell size={32} className="text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Notifications</h3>
            <p className="text-gray-400">You don't have any notifications yet</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              className={`card border-l-4 ${getNotificationColor(notification.type)} ${notification.read ? 'opacity-60' : ''}`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  {getNotificationIcon(notification.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-white">{notification.title}</h3>
                      <span className="badge badge-info text-xs">{notification.type}</span>
                    </div>
                    <span className="text-xs text-gray-400">{formatTime(notification.createdAt)}</span>
                  </div>
                  <p className="text-gray-400 text-sm">{notification.message}</p>
                  {notification.data && (
                    <div className="mt-3 p-3 bg-gray-800 rounded-lg text-xs text-gray-300">
                      <pre>{JSON.stringify(notification.data, null, 2)}</pre>
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0">
                  {!notification.read && (
                    <button
                      onClick={() => onMarkAsRead(notification.id)}
                      className="btn btn-sm btn-secondary p-2"
                      title="Mark as read"
                    >
                      <Check size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Notifications;
