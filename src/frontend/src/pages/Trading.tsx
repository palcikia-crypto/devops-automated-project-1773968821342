import React, { useState } from 'react';
import { DollarSign, Target, Shield, Rocket, TrendingUp, TrendingDown, Clock, Check, X } from 'lucide-react';

const Trading: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'paper' | 'real'>('paper');
  const [tradeType, setTradeType] = useState<'buy' | 'sell'>('buy');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [stopLoss, setStopLoss] = useState<string>('');
  const [takeProfit, setTakeProfit] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Trade submitted:', { tradeType, amount, price, stopLoss, takeProfit });
    // In a real app, this would submit the trade to the API
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Trading</h1>
        <p className="text-gray-400">Execute trades on Polymarket</p>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('paper')}
            className={`px-4 py-2 font-medium ${activeTab === 'paper' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            Paper Trading
          </button>
          <button
            onClick={() => setActiveTab('real')}
            className={`px-4 py-2 font-medium ${activeTab === 'real' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            Real Trading
          </button>
        </div>

        {activeTab === 'paper' ? (
          <div className="space-y-6">
            <div className="bg-amber-900/20 border border-amber-800 rounded-lg p-4">
              <p className="text-amber-400 text-sm">
                <Shield size={16} className="inline mr-1" />
                Paper trading uses virtual funds. No real money is at risk.
              </p>
            </div>

            {/* Trade Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Trade Type</label>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setTradeType('buy')}
                      className={`flex-1 btn ${tradeType === 'buy' ? 'btn-success' : 'btn-secondary'}`}
                    >
                      <TrendingUp size={16} /> Buy
                    </button>
                    <button
                      type="button"
                      onClick={() => setTradeType('sell')}
                      className={`flex-1 btn ${tradeType === 'sell' ? 'btn-danger' : 'btn-secondary'}`}
                    >
                      <TrendingDown size={16} /> Sell
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Amount (pUSD)</label>
                  <div className="relative">
                    <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="0.00"
                      className="input pl-10"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Price</label>
                  <div className="relative">
                    <Target size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      placeholder="0.0000"
                      step="0.0001"
                      min="0"
                      max="1"
                      className="input pl-10"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Stop Loss</label>
                  <div className="relative">
                    <Shield size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      value={stopLoss}
                      onChange={(e) => setStopLoss(e.target.value)}
                      placeholder="0.00"
                      step="0.01"
                      className="input pl-10"
                    />
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-400 mb-2">Take Profit</label>
                  <div className="relative">
                    <Rocket size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="number"
                      value={takeProfit}
                      onChange={(e) => setTakeProfit(e.target.value)}
                      placeholder="0.00"
                      step="0.01"
                      className="input pl-10"
                    />
                  </div>
                </div>
              </div>

              <button type="submit" className="btn btn-primary w-full">
                <Rocket size={18} /> Execute {tradeType === 'buy' ? 'Buy' : 'Sell'} Order
              </button>
            </form>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-gray-700">
              <button className="btn btn-secondary flex items-center justify-center gap-2 h-12">
                <Target size={18} /> Market Order
              </button>
              <button className="btn btn-secondary flex items-center justify-center gap-2 h-12">
                <Clock size={18} /> Limit Order
              </button>
              <button className="btn btn-secondary flex items-center justify-center gap-2 h-12">
                <Shield size={18} /> Stop Order
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
              <p className="text-red-400 text-sm">
                <Shield size={16} className="inline mr-1" />
                Real trading uses actual funds. Please ensure you understand the risks.
              </p>
            </div>

            <div className="card text-center py-12">
              <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <DollarSign size={32} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Connect Wallet</h3>
              <p className="text-gray-400 mb-6">
                Connect your wallet to start trading with real funds
              </p>
              <button className="btn btn-primary">
                <Rocket size={18} /> Connect Wallet
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Trade History */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Trade History</h3>
          <button className="btn btn-sm btn-secondary">
            View All
          </button>
        </div>
        <div className="text-center py-8 text-gray-400">
          <p>No trades executed yet</p>
          <p className="text-sm mt-2">Your trades will appear here</p>
        </div>
      </div>
    </div>
  );
};

export default Trading;
