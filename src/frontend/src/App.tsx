import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Socket, io } from 'socket.io-client';
import { Home, BarChart3, TrendingUp, Bell, Settings, Rocket, Shield, History } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Markets from './pages/Markets';
import Signals from './pages/Signals';
import Trading from './pages/Trading';
import Portfolio from './pages/Portfolio';
import SettingsPage from './pages/Settings';
import Notifications from './pages/Notifications';

// Types
interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

interface Market {
  id: string;
  title: string;
  slug: string;
  category: string;
  outcomePrices: number[];
  volume24hr: number;
  liquidity: number;
  status: string;
}

interface Signal {
  id: string;
  type: string;
  marketTitle: string;
  outcome: string;
  edge: number;
  price: number;
  strategy: string;
  status: string;
  createdAt: string;
}

interface PortfolioData {
  balance: number;
  totalValue: number;
  unrealizedPnl: number;
  realizedPnl: number;
  totalPnl: number;
  returnPct: number;
  positions: number;
}

const App: React.FC = () => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('http://localhost:8000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to WebSocket');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from WebSocket');
    });

    newSocket.on('notification', (data: Notification) => {
      setNotifications(prev => [data, ...prev]);
      if (!data.read) {
        setUnreadCount(prev => prev + 1);
      }
    });

    newSocket.on('portfolio_update', (data: PortfolioData) => {
      setPortfolio(data);
    });

    return () => {
      newSocket.disconnect();
    };
  }, []);

  // Fetch initial data
  useEffect(() => {
    fetchPortfolio();
    fetchNotifications();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/paper/portfolio/snapshot');
      const data = await response.json();
      setPortfolio(data);
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/notifications?limit=20');
      const data = await response.json();
      setNotifications(data);
      const unread = data.filter((n: Notification) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markNotificationAsRead = async (id: string) => {
    try {
      await fetch(`http://localhost:8000/api/dashboard/notifications/${id}/read`, {
        method: 'POST',
      });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch('http://localhost:8000/api/dashboard/notifications/read-all', {
        method: 'POST',
      });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Navigation items
  const navItems = [
    { path: '/', icon: <Home size={18} />, label: 'Dashboard' },
    { path: '/markets', icon: <BarChart3 size={18} />, label: 'Markets' },
    { path: '/signals', icon: <TrendingUp size={18} />, label: 'Signals' },
    { path: '/trading', icon: <Rocket size={18} />, label: 'Trading' },
    { path: '/portfolio', icon: <Shield size={18} />, label: 'Portfolio' },
    { path: '/history', icon: <History size={18} />, label: 'History' },
    { path: '/settings', icon: <Settings size={18} />, label: 'Settings' },
  ];

  return (
    <Router>
      <div className="min-h-screen bg-gray-900 text-slate-200 flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col fixed h-full z-10">
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-cyan-600 rounded-lg flex items-center justify-center">
                <Rocket size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Polymarket Lab</h1>
                <p className="text-xs text-gray-400">Crypto Trading</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors hover:bg-gray-700/50"
              >
                <span className="text-gray-400">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Portfolio Summary in Sidebar */}
          {portfolio && (
            <div className="p-4 border-t border-gray-700">
              <div className="card p-4">
                <p className="text-xs text-gray-400 mb-1">Portfolio</p>
                <p className="text-xl font-bold text-white">${portfolio.balance?.toFixed(2)}</p>
                <p className="text-xs text-cyan-400">
                  {portfolio.returnPct >= 0 ? '+' : ''}{portfolio.returnPct?.toFixed(2)}%
                </p>
              </div>
            </div>
          )}

          {/* Connection Status */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center gap-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-red-500'}`} />
              <span className={isConnected ? 'text-emerald-400' : 'text-red-400'}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 ml-64">
          {/* Header */}
          <header className="sticky top-0 bg-gray-900/80 backdrop-blur-lg z-10 border-b border-gray-700">
            <div className="flex items-center justify-between px-6 py-4">
              <div />
              <div className="flex items-center gap-4">
                {/* Notifications */}
                <button
                  className="relative p-2 rounded-lg hover:bg-gray-800 transition-colors"
                  onClick={() => markAllAsRead()}
                >
                  <Bell size={20} className="text-gray-400" />
                  {unreadCount > 0 && (
                    <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center text-white font-medium">
                      {unreadCount}
                    </span>
                  )}
                </button>

                {/* User Menu */}
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium">U</span>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <div className="p-6">
            <Routes>
              <Route path="/" element={<Dashboard socket={socket} portfolio={portfolio} />} />
              <Route path="/markets" element={<Markets />} />
              <Route path="/signals" element={<Signals />} />
              <Route path="/trading" element={<Trading />} />
              <Route path="/portfolio" element={<Portfolio portfolio={portfolio} />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/notifications" element={<Notifications notifications={notifications} onMarkAsRead={markNotificationAsRead} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
};

export default App;
