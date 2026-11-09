import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Clock, Target, DollarSign, Percentage, Filter, Search, ArrowUpDown, Rocket } from 'lucide-react';

interface Signal {
  id: string;
  type: string;
  marketId: string;
  marketTitle: string;
  marketSlug: string;
  outcome: string;
  outcomeIndex?: number;
  entryPrice: number;
  currentPrice: number;
  targetPrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  edge: number;
  arbitrage?: number;
  growth?: number;
  correlation?: number;
  sentimentScore?: number;
  positionSize: number;
  riskPerTrade: number;
  status: string;
  pnl?: number;
  pnlPct?: number;
  strategy: string;
  createdAt: string;
  updatedAt?: string;
  closedAt?: string;
}

const Signals: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [strategyFilter, setStrategyFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('edge');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchSignals();
  }, [searchQuery, typeFilter, statusFilter, strategyFilter, sortBy, sortOrder]);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      
      let url = `http://localhost:8000/api/signals?limit=100`;
      
      if (typeFilter !== 'all') {
        url += `&signal_type=${typeFilter}`;
      }
      if (statusFilter !== 'all') {
        url += `&status=${statusFilter}`;
      }
      if (strategyFilter !== 'all') {
        url += `&strategy=${strategyFilter}`;
      }
      
      url += `&sort_by=${sortBy}&sort_order=${sortOrder}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      // Filter by search query
      let filteredSignals = data;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filteredSignals = filteredSignals.filter(
          (signal: Signal) => 
            signal.marketTitle.toLowerCase().includes(query) ||
            signal.outcome.toLowerCase().includes(query) ||
            signal.strategy.toLowerCase().includes(query)
        );
      }

      setSignals(filteredSignals);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch signals');
      setLoading(false);
    }
  };

  const toggleSortOrder = () => {
    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
  };

  const getSignalTypes = () => {
    const types = new Set<string>();
    signals.forEach(signal => types.add(signal.type));
    return ['all', ...Array.from(types)];
  };

  const getSignalStatuses = () => {
    const statuses = new Set<string>();
    signals.forEach(signal => statuses.add(signal.status));
    return ['all', ...Array.from(statuses)];
  };

  const getStrategies = () => {
    const strategies = new Set<string>();
    signals.forEach(signal => strategies.add(signal.strategy));
    return ['all', ...Array.from(strategies)];
  };

  const formatNumber = (num: number | undefined) => {
    if (num === undefined) return 'N/A';
    return num.toLocaleString(undefined, { 
      maximumFractionDigits: num > 100 ? 2 : 4 
    });
  };

  const formatEdge = (edge: number) => {
    return (edge * 100).toFixed(2) + '%';
  };

  const formatPnl = (pnl: number | undefined) => {
    if (pnl === undefined) return 'N/A';
    const isPositive = pnl >= 0;
    return (
      <span className={isPositive ? 'text-emerald-400' : 'text-red-400'}>
        {isPositive ? '+' : ''}${pnl.toFixed(2)}
      </span>
    );
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'text-emerald-400';
      case 'pending':
        return 'text-amber-400';
      case 'closed':
        return 'text-gray-400';
      case 'expired':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'undervalued':
        return <TrendingUp size={16} />;
      case 'arbitrage':
        return <Target size={16} />;
      case 'trending':
        return <TrendingUp size={16} />;
      case 'correlation':
        return <Percentage size={16} />;
      case 'liquidity':
        return <DollarSign size={16} />;
      case 'sentiment':
        return <TrendingUp size={16} />;
      case 'seasonality':
        return <Clock size={16} />;
      case 'mean_reversion':
        return <TrendingDown size={16} />;
      case 'breakout':
        return <TrendingUp size={16} />;
      case 'volume_spike':
        return <DollarSign size={16} />;
      default:
        return <Target size={16} />;
    }
  };

  const handleTrade = (signal: Signal) => {
    console.log('Trading signal:', signal);
    // In a real app, this would execute the trade
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card h-20 animate-pulse bg-gray-800/50" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-red-400">
        <p>Error: {error}</p>
        <button onClick={fetchSignals} className="btn btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Signals</h1>
        <p className="text-gray-400">Trading signals generated by our automated strategies</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search signals..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="input"
          >
            {getSignalTypes().map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
          >
            {getSignalStatuses().map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={strategyFilter}
            onChange={(e) => setStrategyFilter(e.target.value)}
            className="input"
          >
            {getStrategies().map((strategy) => (
              <option key={strategy} value={strategy}>
                {strategy}
              </option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input"
          >
            <option value="edge">Edge</option>
            <option value="created_at">Date</option>
            <option value="pnl">PnL</option>
            <option value="position_size">Position Size</option>
          </select>
          <button
            onClick={toggleSortOrder}
            className="btn btn-secondary flex items-center gap-2"
          >
            <ArrowUpDown size={18} />
            {sortOrder === 'asc' ? 'Asc' : 'Desc'}
          </button>
        </div>
      </div>

      {/* Signals Table */}
      <div className="card overflow-x-auto">
        <table className="table w-full">
          <thead>
            <tr>
              <th>Signal</th>
              <th>Type</th>
              <th>Market</th>
              <th>Outcome</th>
              <th>Edge</th>
              <th>Entry Price</th>
              <th>Current Price</th>
              <th>PnL</th>
              <th>Status</th>
              <th>Strategy</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((signal) => (
              <tr key={signal.id} className="hover:bg-gray-800/50 transition-colors">
                <td>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-400">{getTypeIcon(signal.type)}</span>
                    <span className="text-xs text-gray-500">{signal.id.slice(0, 8)}</span>
                  </div>
                </td>
                <td>
                  <span className="badge badge-info text-xs">
                    {signal.type}
                  </span>
                </td>
                <td>
                  <div>
                    <p className="text-white font-medium">{signal.marketTitle}</p>
                    <p className="text-xs text-gray-400">{signal.marketSlug}</p>
                  </div>
                </td>
                <td>
                  <span className="text-gray-300">{signal.outcome}</span>
                </td>
                <td>
                  <span className="text-emerald-400 font-medium">
                    {formatEdge(signal.edge)}
                  </span>
                </td>
                <td>
                  <span className="text-gray-300">{formatNumber(signal.entryPrice)}</span>
                </td>
                <td>
                  <span className="text-gray-300">{formatNumber(signal.currentPrice)}</span>
                </td>
                <td>
                  {formatPnl(signal.pnl)}
                </td>
                <td>
                  <span className={`font-medium ${getStatusColor(signal.status)}`}>
                    {signal.status}
                  </span>
                </td>
                <td>
                  <span className="text-gray-300 text-xs">{signal.strategy}</span>
                </td>
                <td>
                  <button
                    onClick={() => handleTrade(signal)}
                    className="btn btn-sm btn-primary flex items-center gap-1"
                  >
                    <Rocket size={14} /> Trade
                  </button>
                </td>
              </tr>
            ))}
            {signals.length === 0 && (
              <tr>
                <td colSpan={11} className="text-center py-8 text-gray-400">
                  No signals found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div className="stat-card">
          <p className="stat-value">{signals.length}</p>
          <p className="stat-label">Total Signals</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            {signals.filter(s => s.status === 'active').length}
          </p>
          <p className="stat-label">Active</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            {signals.filter(s => s.status === 'closed').length}
          </p>
          <p className="stat-label">Closed</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            {getStrategies().length - 1}
          </p>
          <p className="stat-label">Strategies</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            {formatEdge(signals.reduce((sum, s) => sum + s.edge, 0) / signals.length || 0)}
          </p>
          <p className="stat-label">Avg Edge</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            <DollarSign size={20} className="inline" />
            {formatNumber(signals.reduce((sum, s) => sum + (s.pnl || 0), 0))}
          </p>
          <p className="stat-label">Total PnL</p>
        </div>
      </div>
    </div>
  );
};

export default Signals;
