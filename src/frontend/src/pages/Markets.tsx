import React, { useState, useEffect } from 'react';
import { Search, Filter, ArrowUpDown, Activity, DollarSign, Clock, Users } from 'lucide-react';

interface Market {
  id: string;
  title: string;
  slug: string;
  category: string;
  subcategory?: string;
  outcomePrices: number[];
  volume24hr: number;
  volume1wk: number;
  volume1mo: number;
  liquidity: number;
  endDate?: string;
  status: string;
  fee: number;
}

const Markets: React.FC = () => {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('volume');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchMarkets();
  }, [searchQuery, categoryFilter, sortBy, sortOrder]);

  const fetchMarkets = async () => {
    try {
      setLoading(true);
      
      let url = `http://localhost:8000/api/markets?limit=100&tag_id=21`;
      
      if (categoryFilter !== 'all') {
        url += `&category=${encodeURIComponent(categoryFilter)}`;
      }
      
      const response = await fetch(url);
      const data = await response.json();
      
      // Filter by search query
      let filteredMarkets = data;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filteredMarkets = filteredMarkets.filter(
          (market: Market) => 
            market.title.toLowerCase().includes(query) ||
            market.category.toLowerCase().includes(query) ||
            market.slug.toLowerCase().includes(query)
        );
      }

      // Sort markets
      filteredMarkets = filteredMarkets.sort((a: Market, b: Market) => {
        let aValue: number, bValue: number;
        
        switch (sortBy) {
          case 'volume':
            aValue = a.volume24hr;
            bValue = b.volume24hr;
            break;
          case 'liquidity':
            aValue = a.liquidity;
            bValue = b.liquidity;
            break;
          case 'fee':
            aValue = a.fee;
            bValue = b.fee;
            break;
          case 'title':
            return sortOrder === 'asc' 
              ? a.title.localeCompare(b.title) 
              : b.title.localeCompare(a.title);
          default:
            aValue = a.volume24hr;
            bValue = b.volume24hr;
        }
        
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      });

      setMarkets(filteredMarkets);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch markets');
      setLoading(false);
    }
  };

  const toggleSortOrder = () => {
    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
  };

  const getCategories = () => {
    const categories = new Set<string>();
    markets.forEach(market => {
      if (market.category) categories.add(market.category);
      if (market.subcategory) categories.add(market.subcategory);
    });
    return ['all', ...Array.from(categories)];
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString(undefined, { 
      maximumFractionDigits: num > 1000 ? 0 : 2 
    });
  };

  const formatPrice = (prices: number[]) => {
    if (!prices || prices.length === 0) return 'N/A';
    return prices.map(p => p.toFixed(2)).join(' / ');
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'text-emerald-400';
      case 'closed':
        return 'text-red-400';
      case 'resolved':
        return 'text-purple-400';
      default:
        return 'text-gray-400';
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="card h-16 animate-pulse bg-gray-800/50" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-red-400">
        <p>Error: {error}</p>
        <button onClick={fetchMarkets} className="btn btn-primary mt-4">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Markets</h1>
        <p className="text-gray-400">Browse crypto prediction markets on Polymarket</p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search markets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="input"
          >
            {getCategories().map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input"
          >
            <option value="volume">Volume (24h)</option>
            <option value="liquidity">Liquidity</option>
            <option value="fee">Fee</option>
            <option value="title">Title</option>
          </select>
          <button
            onClick={toggleSortOrder}
            className="btn btn-secondary flex items-center gap-2"
          >
            <ArrowUpDown size={18} />
            {sortOrder === 'asc' ? 'Ascending' : 'Descending'}
          </button>
        </div>
      </div>

      {/* Markets Table */}
      <div className="card overflow-x-auto">
        <table className="table w-full">
          <thead>
            <tr>
              <th>Market</th>
              <th>Category</th>
              <th>Prices</th>
              <th>Volume (24h)</th>
              <th>Liquidity</th>
              <th>Fee</th>
              <th>End Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {markets.map((market) => (
              <tr key={market.id} className="hover:bg-gray-800/50 transition-colors">
                <td>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-700 rounded-lg flex items-center justify-center">
                      <Activity size={16} className="text-gray-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">{market.title}</p>
                      <p className="text-xs text-gray-400">{market.slug}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="text-gray-300">{market.category}</span>
                  {market.subcategory && (
                    <span className="text-gray-500 text-xs block">{market.subcategory}</span>
                  )}
                </td>
                <td>
                  <div className="flex gap-1 flex-wrap">
                    {market.outcomePrices?.map((price, index) => (
                      <span key={index} className="badge badge-info">
                        {price.toFixed(2)}
                      </span>
                    ))}
                  </div>
                </td>
                <td>
                  <span className="text-white">
                    <DollarSign size={14} className="inline mr-1" />
                    {formatNumber(market.volume24hr)}
                  </span>
                </td>
                <td>
                  <span className="text-white">
                    <DollarSign size={14} className="inline mr-1" />
                    {formatNumber(market.liquidity)}
                  </span>
                </td>
                <td>
                  <span className="text-gray-300">{market.fee}%</span>
                </td>
                <td>
                  {market.endDate ? (
                    <span className="text-gray-300">
                      {new Date(market.endDate).toLocaleDateString()}
                    </span>
                  ) : (
                    <span className="text-gray-500">N/A</span>
                  )}
                </td>
                <td>
                  <span className={`font-medium ${getStatusColor(market.status)}`}>
                    {market.status}
                  </span>
                </td>
              </tr>
            ))}
            {markets.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-400">
                  No markets found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <p className="stat-value">{markets.length}</p>
          <p className="stat-label">Total Markets</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            <DollarSign size={20} className="inline" />
            {formatNumber(markets.reduce((sum, m) => sum + m.volume24hr, 0))}
          </p>
          <p className="stat-label">Total Volume</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            <DollarSign size={20} className="inline" />
            {formatNumber(markets.reduce((sum, m) => sum + m.liquidity, 0))}
          </p>
          <p className="stat-label">Total Liquidity</p>
        </div>
        <div className="stat-card">
          <p className="stat-value">
            <Users size={20} className="inline" />
            {new Set(markets.map(m => m.category)).size}
          </p>
          <p className="stat-label">Categories</p>
        </div>
      </div>
    </div>
  );
};

export default Markets;
