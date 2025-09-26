import React, { useState, useEffect } from 'react';
import { Save, Bell, Shield, Globe, Monitor, Database } from 'lucide-react';

const API_URL = 'http://localhost:4000/api';

const Settings = () => {
  const [settings, setSettings] = useState({
    notifications: true,
    autoStart: false,
    darkMode: true,
    language: 'en',
    defaultProxy: '',
    maxProfiles: 50,
    sessionTimeout: 30,
    autoBackup: true,
    backupInterval: 24
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_URL}/settings`);
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const handleSave = async () => {
    try {
      const response = await fetch(`${API_URL}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (response.ok) {
        alert('Settings saved successfully!');
      } else {
        alert('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    }
  };

  const handleChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Settings</h1>
        <p className="text-gray-400 mt-1">Configure your application preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* General Settings */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center mb-6">
            <Monitor className="text-blue-400 mr-3" size={24} />
            <h2 className="text-xl font-semibold text-white">General</h2>
          </div>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">Dark Mode</label>
                <p className="text-gray-400 text-sm">Use dark theme interface</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.darkMode}
                  onChange={(e) => handleChange('darkMode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">Auto Start</label>
                <p className="text-gray-400 text-sm">Start application on system boot</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoStart}
                  onChange={(e) => handleChange('autoStart', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Language</label>
              <select
                value={settings.language}
                onChange={(e) => handleChange('language', e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Session Timeout (minutes)</label>
              <input
                type="number"
                value={settings.sessionTimeout}
                onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                min="5"
                max="120"
              />
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center mb-6">
            <Shield className="text-green-400 mr-3" size={24} />
            <h2 className="text-xl font-semibold text-white">Security</h2>
          </div>
          <div className="space-y-6">
            <div>
              <label className="block text-white font-medium mb-2">Default Proxy</label>
              <input
                type="text"
                value={settings.defaultProxy}
                onChange={(e) => handleChange('defaultProxy', e.target.value)}
                placeholder="http://proxy.example.com:8080"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
              />
              <p className="text-gray-400 text-sm mt-1">Default proxy for new profiles</p>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Max Profiles</label>
              <input
                type="number"
                value={settings.maxProfiles}
                onChange={(e) => handleChange('maxProfiles', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                min="1"
                max="1000"
              />
              <p className="text-gray-400 text-sm mt-1">Maximum number of profiles allowed</p>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">Auto Backup</label>
                <p className="text-gray-400 text-sm">Automatically backup profile data</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.autoBackup}
                  onChange={(e) => handleChange('autoBackup', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {settings.autoBackup && (
              <div>
                <label className="block text-white font-medium mb-2">Backup Interval (hours)</label>
                <input
                  type="number"
                  value={settings.backupInterval}
                  onChange={(e) => handleChange('backupInterval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                  min="1"
                  max="168"
                />
              </div>
            )}
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center mb-6">
            <Bell className="text-yellow-400 mr-3" size={24} />
            <h2 className="text-xl font-semibold text-white">Notifications</h2>
          </div>
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">Enable Notifications</label>
                <p className="text-gray-400 text-sm">Receive system notifications</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifications}
                  onChange={(e) => handleChange('notifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center mb-6">
            <Database className="text-purple-400 mr-3" size={24} />
            <h2 className="text-xl font-semibold text-white">Data Management</h2>
          </div>
          <div className="space-y-4">
            <button className="w-full px-4 py-3 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-colors text-left">
              Export Profile Data
            </button>
            <button className="w-full px-4 py-3 bg-green-600/20 text-green-300 rounded-lg hover:bg-green-600/30 transition-colors text-left">
              Import Profile Data
            </button>
            <button className="w-full px-4 py-3 bg-yellow-600/20 text-yellow-300 rounded-lg hover:bg-yellow-600/30 transition-colors text-left">
              Clear Cache
            </button>
            <button className="w-full px-4 py-3 bg-red-600/20 text-red-300 rounded-lg hover:bg-red-600/30 transition-colors text-left">
              Reset All Settings
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={handleSave}
          className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
        >
          <Save size={20} />
          <span>Save Settings</span>
        </button>
      </div>
    </div>
  );
};

export default Settings;