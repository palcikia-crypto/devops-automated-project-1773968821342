import React, { useState } from 'react';
import { Settings as SettingsIcon, Bell, DollarSign, Shield, Rocket, User, Save, X, Trash2 } from 'lucide-react';

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'general' | 'trading' | 'notifications' | 'api' | 'danger'>('general');
  const [settings, setSettings] = useState({
    // General
    theme: 'dark',
    language: 'en',
    timezone: 'UTC',
    
    // Trading
    paperTradingEnabled: true,
    realTradingEnabled: false,
    autoTrade: false,
    maxPositionSize: 1000,
    maxPortfolioRisk: 5,
    stopLossPct: 10,
    takeProfitPct: 20,
    
    // Notifications
    telegramEnabled: false,
    telegramBotToken: '',
    telegramChatId: '',
    discordEnabled: false,
    discordWebhookUrl: '',
    desktopNotifications: true,
    soundEnabled: true,
    
    // API
    polymarketApiKey: '',
    coingeckoApiKey: '',
    twitterApiKey: '',
    newsApiKey: '',
    
    // Paper Trading
    initialBalance: 10000,
  });

  const handleSave = () => {
    console.log('Settings saved:', settings);
    // In a real app, this would save to the API
  };

  const handleReset = () => {
    // Reset to default settings
    setSettings({
      theme: 'dark',
      language: 'en',
      timezone: 'UTC',
      paperTradingEnabled: true,
      realTradingEnabled: false,
      autoTrade: false,
      maxPositionSize: 1000,
      maxPortfolioRisk: 5,
      stopLossPct: 10,
      takeProfitPct: 20,
      telegramEnabled: false,
      telegramBotToken: '',
      telegramChatId: '',
      discordEnabled: false,
      discordWebhookUrl: '',
      desktopNotifications: true,
      soundEnabled: true,
      polymarketApiKey: '',
      coingeckoApiKey: '',
      twitterApiKey: '',
      newsApiKey: '',
      initialBalance: 10000,
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;
    
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-gray-400">Configure your Polymarket Crypto Lab</p>
      </div>

      <div className="card">
        {/* Tabs */}
        <div className="flex border-b border-gray-700 mb-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'general' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            <SettingsIcon size={16} className="inline mr-2" />
            General
          </button>
          <button
            onClick={() => setActiveTab('trading')}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'trading' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            <DollarSign size={16} className="inline mr-2" />
            Trading
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'notifications' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            <Bell size={16} className="inline mr-2" />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab('api')}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'api' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            <User size={16} className="inline mr-2" />
            API Keys
          </button>
          <button
            onClick={() => setActiveTab('danger')}
            className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'danger' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-gray-400 hover:text-white'}`}
          >
            <Shield size={16} className="inline mr-2" />
            Danger Zone
          </button>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">General Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Theme</label>
                  <select
                    name="theme"
                    value={settings.theme}
                    onChange={handleInputChange}
                    className="input"
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="system">System</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Language</label>
                  <select
                    name="language"
                    value={settings.language}
                    onChange={handleInputChange}
                    className="input"
                  >
                    <option value="en">English</option>
                    <option value="ru">Russian</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Timezone</label>
                  <select
                    name="timezone"
                    value={settings.timezone}
                    onChange={handleInputChange}
                    className="input"
                  >
                    <option value="UTC">UTC</option>
                    <option value="EST">EST (UTC-5)</option>
                    <option value="PST">PST (UTC-8)</option>
                    <option value="CET">CET (UTC+1)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'trading' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">Trading Settings</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Paper Trading</label>
                    <p className="text-xs text-gray-500">Trade with virtual funds</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="paperTradingEnabled"
                      checked={settings.paperTradingEnabled}
                      onChange={handleInputChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Real Trading</label>
                    <p className="text-xs text-gray-500">Trade with real funds (requires wallet)</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="realTradingEnabled"
                      checked={settings.realTradingEnabled}
                      onChange={handleInputChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Auto-Trading</label>
                    <p className="text-xs text-gray-500">Automatically execute trades from signals</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="autoTrade"
                      checked={settings.autoTrade}
                      onChange={handleInputChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-700">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Max Position Size (pUSD)</label>
                    <div className="relative">
                      <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="number"
                        name="maxPositionSize"
                        value={settings.maxPositionSize}
                        onChange={handleInputChange}
                        className="input pl-10"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Max Portfolio Risk (%)</label>
                    <div className="relative">
                      <Percentage size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="number"
                        name="maxPortfolioRisk"
                        value={settings.maxPortfolioRisk}
                        onChange={handleInputChange}
                        className="input pl-10"
                        min="0"
                        max="100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Stop Loss (%)</label>
                    <div className="relative">
                      <Shield size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="number"
                        name="stopLossPct"
                        value={settings.stopLossPct}
                        onChange={handleInputChange}
                        className="input pl-10"
                        min="0"
                        max="100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Take Profit (%)</label>
                    <div className="relative">
                      <Rocket size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="number"
                        name="takeProfitPct"
                        value={settings.takeProfitPct}
                        onChange={handleInputChange}
                        className="input pl-10"
                        min="0"
                        max="100"
                      />
                    </div>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-400 mb-2">Initial Paper Balance (pUSD)</label>
                    <div className="relative">
                      <DollarSign size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="number"
                        name="initialBalance"
                        value={settings.initialBalance}
                        onChange={handleInputChange}
                        className="input pl-10"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">Notification Settings</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Desktop Notifications</label>
                    <p className="text-xs text-gray-500">Show notifications in your browser</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="desktopNotifications"
                      checked={settings.desktopNotifications}
                      onChange={handleInputChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Sound Notifications</label>
                    <p className="text-xs text-gray-500">Play sound for notifications</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="soundEnabled"
                      checked={settings.soundEnabled}
                      onChange={handleInputChange}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                  </label>
                </div>

                <div className="pt-4 border-t border-gray-700 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Telegram Notifications</label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        name="telegramEnabled"
                        checked={settings.telegramEnabled}
                        onChange={handleInputChange}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                    </label>
                  </div>

                  {settings.telegramEnabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Bot Token</label>
                        <input
                          type="password"
                          name="telegramBotToken"
                          value={settings.telegramBotToken}
                          onChange={handleInputChange}
                          placeholder="Enter bot token"
                          className="input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Chat ID</label>
                        <input
                          type="text"
                          name="telegramChatId"
                          value={settings.telegramChatId}
                          onChange={handleInputChange}
                          placeholder="Enter chat ID"
                          className="input"
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-1">Discord Notifications</label>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        name="discordEnabled"
                        checked={settings.discordEnabled}
                        onChange={handleInputChange}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-600"></div>
                    </label>
                  </div>

                  {settings.discordEnabled && (
                    <div>
                      <label className="block text-sm font-medium text-gray-400 mb-2">Webhook URL</label>
                      <input
                        type="text"
                        name="discordWebhookUrl"
                        value={settings.discordWebhookUrl}
                        onChange={handleInputChange}
                        placeholder="Enter webhook URL"
                        className="input"
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">API Keys</h3>
              <p className="text-gray-400 text-sm">Configure external API keys for enhanced functionality</p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Polymarket API Key</label>
                  <input
                    type="password"
                    name="polymarketApiKey"
                    value={settings.polymarketApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter Polymarket API key"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">CoinGecko API Key</label>
                  <input
                    type="password"
                    name="coingeckoApiKey"
                    value={settings.coingeckoApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter CoinGecko API key"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Twitter API Key</label>
                  <input
                    type="password"
                    name="twitterApiKey"
                    value={settings.twitterApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter Twitter API key"
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">NewsAPI Key</label>
                  <input
                    type="password"
                    name="newsApiKey"
                    value={settings.newsApiKey}
                    onChange={handleInputChange}
                    placeholder="Enter NewsAPI key"
                    className="input"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'danger' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">Danger Zone</h3>
              <p className="text-gray-400 text-sm">These actions cannot be undone</p>
              
              <div className="space-y-4">
                <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-white mb-1">Reset Paper Trading</h4>
                      <p className="text-sm text-gray-400">This will reset your paper trading balance and clear all positions and trades</p>
                    </div>
                    <button className="btn btn-danger">
                      <Trash2 size={16} /> Reset
                    </button>
                  </div>
                </div>

                <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-white mb-1">Clear All Data</h4>
                      <p className="text-sm text-gray-400">This will clear all cached data, signals, and market history</p>
                    </div>
                    <button className="btn btn-danger">
                      <Trash2 size={16} /> Clear
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-6 border-t border-gray-700">
          <button onClick={handleReset} className="btn btn-secondary">
            <X size={18} /> Reset
          </button>
          <button onClick={handleSave} className="btn btn-primary">
            <Save size={18} /> Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
