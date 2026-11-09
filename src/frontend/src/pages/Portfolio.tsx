import React from 'react';
import { DollarSign, TrendingUp, TrendingDown, Clock, Shield, Percentage, BarChart3, History } from 'lucide-react';

interface PortfolioProps {
  portfolio: any;
}

interface Position {
  id: string;
  marketId: string;
  marketTitle: string;
  outcome: string;
  side: 'buy' | 'sell';
  amount: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  stopLoss?: number;
  takeProfit?: number;
  createdAt: string;
}

const Portfolio: React.FC<PortfolioProps> = ({ portfolio }) => {
  const positions: Position[] = []; // In a real app, fetch from API

  const formatNumber = (num: number | undefined) => {
    if (num === undefined) return '0.00';
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  const formatPnl = (pnl: number | undefined) => {
    if (pnl === undefined) return '0.00';
    const isPositive = pnl >= 0;
    return (
      <span className={isPositive ? 'text-emerald-400' : 'text-red-400'}>
        {isPositive ? '+' : ''}${formatNumber(pnl)}
      </span>
    );
  };

  const getSideColor = (side: 'buy' | 'sell') => {
    return side === 'buy' ? 'text-emerald-400' : 'text-red-400';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Portfolio</h1>
        <p className="text-gray-400">Track your positions and performance</p>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-cyan-900/30 rounded-lg flex items-center justify-center">
              <DollarSign size={20} className="text-cyan-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Balance</p>
              <p className="text-2xl font-bold text-white">${formatNumber(portfolio?.balance)}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-emerald-900/30 rounded-lg flex items-center justify-center">
              <TrendingUp size={20} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Unrealized PnL</p>
              <p className="text-2xl font-bold text-emerald-400">
                {formatPnl(portfolio?.unrealizedPnl)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-900/30 rounded-lg flex items-center justify-center">
              <Percentage size={20} className="text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Realized PnL</p>
              <p className="text-2xl font-bold text-purple-400">
                {formatPnl(portfolio?.realizedPnl)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-amber-900/30 rounded-lg flex items-center justify-center">
              <Shield size={20} className="text-amber-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total PnL</p>
              <p className="text-2xl font-bold text-white">
                {formatPnl(portfolio?.totalPnl)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-6">Performance Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="stat-card">
            <p className="stat-value">{positions.length}</p>
            <p className="stat-label">Open Positions</p>
          </div>
          <div className="stat-card">
            <p className="stat-value">
              {portfolio?.returnPct >= 0 ? '+' : ''}{portfolio?.returnPct?.toFixed(2) || '0.00'}%
            </p>
            <p className="stat-label">Return %</p>
          </div>
          <div className="stat-card">
            <p className="stat-value">0</p>
            <p className="stat-label">Win Rate</p>
          </div>
          <div className="stat-card">
            <p className="stat-value">0</p>
            <p className="stat-label">Total Trades</p>
          </div>
          <div className="stat-card">
            <p className="stat-value">$0.00</p>
            <p className="stat-label">Avg PnL</p>
          </div>
          <div className="stat-card">
            <p className="stat-value">$0.00</p>
            <p className="stat-label">Max Drawdown</p>
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Open Positions</h3>
          <button className="btn btn-sm btn-secondary">
            <History size={14} /> View History
          </button>
        </div>
        
        {positions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>No open positions</p>
            <p className="text-sm mt-2">Your open positions will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr>
                  <th>Market</th>
                  <th>Outcome</th>
                  <th>Side</th>
                  <th>Entry Price</th>
                  <th>Current Price</th>
                  <th>Amount</th>
                  <th>PnL</th>
                  <th>PnL %</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => (
                  <tr key={position.id} className="hover:bg-gray-800/50 transition-colors">
                    <td>
                      <p className="text-white font-medium">{position.marketTitle}</p>
                    </td>
                    <td>
                      <span className="text-gray-300">{position.outcome}</span>
                    </td>
                    <td>
                      <span className={`font-medium ${getSideColor(position.side)}`}>
                        {position.side.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className="text-gray-300">{formatNumber(position.entryPrice)}</span>
                    </td>
                    <td>
                      <span className="text-gray-300">{formatNumber(position.currentPrice)}</span>
                    </td>
                    <td>
                      <span className="text-white">${formatNumber(position.amount)}</span>
                    </td>
                    <td>
                      {formatPnl(position.pnl)}
                    </td>
                    <td>
                      <span className={position.pnlPct >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                        {position.pnlPct >= 0 ? '+' : ''}{position.pnlPct.toFixed(2)}%
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-sm btn-danger">Close</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Portfolio Chart */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-6">Portfolio Value Over Time</h3>
        <div className="h-64 bg-gray-800 rounded-lg flex items-center justify-center text-gray-400">
          <p>Chart will be displayed here</p>
        </div>
      </div>
    </div>
  );
};

export default Portfolio;
