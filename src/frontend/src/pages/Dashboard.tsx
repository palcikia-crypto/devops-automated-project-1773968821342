import React, { useState, useEffect } from 'react';
import { Socket } from 'socket.io-client';
import { ArrowUp, ArrowDown, TrendingUp, TrendingDown, Clock, Users, Activity, DollarSign, Percentage, Rocket } from 'lucide-react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface DashboardProps {
  socket: Socket | null;
  portfolio: any;
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

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string | number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, changeType = 'neutral', icon, color = 'cyan' }) => {
  const colorMap = {
    cyan: 'text-cyan-400',
    green: 'text-emerald-400',
    red: 'text-red-400',
    orange: 'text-amber-400',
    purple: 'text-purple-400',
  };

  const bgColorMap = {
    cyan: 'bg-cyan-900/30',
    green: 'bg-emerald-900/30',
    red: 'bg-red-900/30',
    orange: 'bg-amber-900/30',
    purple: 'bg-purple-900/30',
  };

  return (
    <div className="card group">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${bgColorMap[color as keyof typeof bgColorMap]}`}>
          <span className={`text-xl ${colorMap[color as keyof typeof colorMap]}`}>{icon}</span>
        </div>
        <span className="text-xs text-gray-400 uppercase tracking-wider">{title}</span>
      </div>
      <div className="space-y-2">
        <p className="text-2xl font-bold text-white">{value}</p>
        {change !== undefined && (
          <p className={`text-sm flex items-center gap-1 ${changeType === 'increase' ? 'text-emerald-400' : changeType === 'decrease' ? 'text-red-400' : 'text-gray-400'}`}>
            {changeType === 'increase' ? <ArrowUp size={14} /> : changeType === 'decrease' ? <ArrowDown size={14} /> : <Clock size={14} />}
            {change}
          </p>
        )}
      </div>
    </div>
  );
};

interface SignalCardProps {
  signal: Signal;
  onTrade: (signal: Signal) => void;
}

const SignalCard: React.FC<SignalCardProps> = ({ signal, onTrade }) => {
  const getSignalColor = (type: string) => {
    const colors = {
      undervalued: 'border-emerald-500',
      arbitrage: 'border-purple-500',
      trending: 'border-cyan-500',
      correlation: 'border-amber-500',
      liquidity: 'border-pink-500',
      sentiment: 'border-rose-500',
      seasonality: 'border-indigo-500',
      mean_reversion: 'border-teal-500',
      breakout: 'border-orange-500',
      volume_spike: 'border-red-500',
    };
    return colors[type as keyof typeof colors] || 'border-gray-500';
  };

  const formatEdge = (edge: number) => {
    return (edge * 100).toFixed(2) + '%';
  };

  return (
    <div className={`card border-l-4 ${getSignalColor(signal.type)} hover:shadow-xl transition-shadow`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-white font-semibold mb-1 line-clamp-1">{signal.marketTitle}</h3>
          <p className="text-sm text-gray-400">{signal.outcome}</p>
        </div>
        <span className="badge badge-info text-xs">{signal.strategy}</span>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <TrendingUp size={14} className="text-emerald-400" />
            <span className="text-emerald-400 font-medium">{formatEdge(signal.edge)}</span>
          </div>
          <div className="flex items-center gap-1">
            <DollarSign size={14} className="text-gray-400" />
            <span className="text-gray-400">{signal.price?.toFixed(4)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock size={14} className="text-gray-400" />
            <span className="text-gray-400 text-xs">{new Date(signal.createdAt).toLocaleString()}</span>
          </div>
        </div>
        <button
          onClick={() => onTrade(signal)}
          className="btn btn-sm btn-primary w-full"
        >
          <Rocket size={14} /> Trade Signal
        </button>
      </div>
    </div>
  );
};

interface MarketRowProps {
  market: Market;
}

const MarketRow: React.FC<MarketRowProps> = ({ market }) => {
  return (
    <tr className="hover:bg-gray-800/50 transition-colors">
      <td className="py-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center">
            <Activity size={16} className="text-gray-400" />
          </div>
          <div>
            <p className="text-white font-medium">{market.title}</p>
            <p className="text-xs text-gray-400">{market.category}</p>
          </div>
        </div>
      </td>
      <td className="py-3">
        <div className="flex gap-1">
          {market.outcomePrices?.slice(0, 3).map((price, index) => (
            <span key={index} className="badge badge-info">
              {price.toFixed(2)}
            </span>
          ))}
        </div>
      </td>
      <td className="py-3">
        <p className="text-white">${market.volume24hr?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
      </td>
      <td className="py-3">
        <p className="text-white">${market.liquidity?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
      </td>
      <td className="py-3">
        <span className={`badge ${market.status === 'active' ? 'badge-success' : market.status === 'closed' ? 'badge-danger' : 'badge-warning'}`}>
          {market.status}
        </span>
      </td>
    </tr>
  );
};

const Dashboard: React.FC<DashboardProps> = ({ socket, portfolio }) => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data on mount
  useEffect(() => {
    fetchData();
    
    // Set up socket listeners
    if (socket) {
      socket.on('market_update', (data: any) => {
        setMarkets(data.data || data);
      });
    }

    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [socket]);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch stats
      const statsResponse = await fetch('http://localhost:8000/api/dashboard/overview');
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Fetch markets
      const marketsResponse = await fetch('http://localhost:8000/api/markets?limit=10&tag_id=21');
      const marketsData = await marketsResponse.json();
      setMarkets(marketsData);

      // Fetch signals
      const signalsResponse = await fetch('http://localhost:8000/api/signals/top?limit=10');
      const signalsData = await signalsResponse.json();
      setSignals(signalsData);

      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      setLoading(false);
    }
  };

  const handleTradeSignal = (signal: Signal) => {
    console.log('Trading signal:', signal);
    // In a real app, this would open a trade modal or execute the trade
  };

  // Chart data
  const portfolioChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    datasets: [
      {
        label: 'Portfolio Value',
        data: [10000, 10500, 11000, 10800, 11500, 12000, 12500, 13000, 13500, 14000, 14500, 15000],
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const volumeChartData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'Volume',
        data: [500000, 750000, 600000, 800000],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        grid: {
          color: '#1e293b',
        },
        ticks: {
          color: '#94a3b8',
        },
      },
      y: {
        grid: {
          color: '#1e293b',
        },
        ticks: {
          color: '#94a3b8',
        },
      },
    },
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card flex-1 h-32 animate-pulse bg-gray-800/50" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card h-64 animate-pulse bg-gray-800/50" />
          <div className="card h-64 animate-pulse bg-gray-800/50" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-red-400">
        <p>Error: {error}</p>
        <button onClick={fetchData} className="btn btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Real-time overview of your Polymarket crypto trading</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Markets"
          value={stats?.markets?.total?.toLocaleString() || '0'}
          change={stats?.markets?.active || '0'}
          changeType="increase"
          icon={<Users size={20} />}
          color="cyan"
        />
        <StatCard
          title="Active Signals"
          value={stats?.signals?.active?.toLocaleString() || '0'}
          change={stats?.signals?.total || '0'}
          changeType="increase"
          icon={<TrendingUp size={20} />}
          color="green"
        />
        <StatCard
          title="Portfolio Value"
          value={`$${portfolio?.totalValue?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || '0'}`}
          change={`${portfolio?.returnPct >= 0 ? '+' : ''}${portfolio?.returnPct?.toFixed(2) || '0'}%`}
          changeType={portfolio?.returnPct >= 0 ? 'increase' : 'decrease'}
          icon={<DollarSign size={20} />}
          color="purple"
        />
        <StatCard
          title="Total PnL"
          value={`$${portfolio?.totalPnl?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || '0'}`}
          change={`${portfolio?.returnPct >= 0 ? '+' : ''}${portfolio?.returnPct?.toFixed(2) || '0'}%`}
          changeType={portfolio?.totalPnl >= 0 ? 'increase' : 'decrease'}
          icon={<Percentage size={20} />}
          color={portfolio?.totalPnl >= 0 ? 'green' : 'red'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="card-title">Portfolio Performance</h3>
          <div className="h-64">
            <Line data={portfolioChartData} options={chartOptions} />
          </div>
        </div>
        <div className="card">
          <h3 className="card-title">Trading Volume</h3>
          <div className="h-64">
            <Line data={volumeChartData} options={chartOptions} />
          </div>
        </div>
      </div>

      {/* Content Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Signals */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="card-title">Top Signals</h3>
            <span className="text-sm text-gray-400">{signals.length} active</span>
          </div>
          <div className="space-y-4">
            {signals.map((signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onTrade={handleTradeSignal}
              />
            ))}
            {signals.length === 0 && (
              <p className="text-gray-400 text-center py-8">No signals found</p>
            )}
          </div>
        </div>

        {/* Recent Markets */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="card-title">Recent Markets</h3>
            <span className="text-sm text-gray-400">{markets.length} markets</span>
          </div>
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr>
                  <th>Market</th>
                  <th>Prices</th>
                  <th>Volume (24h)</th>
                  <th>Liquidity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {markets.slice(0, 5).map((market) => (
                  <MarketRow key={market.id} market={market} />
                ))}
                {markets.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-400">
                      No markets found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h3 className="card-title">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn btn-secondary flex items-center justify-center gap-2 h-12">
            <Activity size={18} /> Scan Markets
          </button>
          <button className="btn btn-secondary flex items-center justify-center gap-2 h-12">
            <TrendingUp size={18} /> Generate Signals
          </button>
          <button className="btn btn-primary flex items-center justify-center gap-2 h-12">
            <Rocket size={18} /> Start Auto-Trading
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
