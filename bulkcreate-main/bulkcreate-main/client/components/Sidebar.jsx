import React, { useState, useEffect } from 'react';
import { Users, Layers, Settings, Shield, BarChart3, Globe, Menu, X } from 'lucide-react';

const API_URL = 'http://localhost:4000/api';

const Sidebar = ({ isCollapsed, setIsCollapsed, currentPage, setCurrentPage }) => {
  const [counts, setCounts] = useState({ profiles: 0, groups: 0, proxies: 0 });

  useEffect(() => {
    fetchCounts();
  }, []);

  const fetchCounts = async () => {
    try {
      const [profilesRes, groupsRes, proxiesRes] = await Promise.all([
        fetch(`${API_URL}/profiles`),
        fetch(`${API_URL}/groups`),
        fetch(`${API_URL}/proxies`)
      ]);
      
      const profiles = await profilesRes.json();
      const groups = await groupsRes.json();
      const proxies = await proxiesRes.json();
      
      setCounts({
        profiles: Object.keys(profiles).length,
        groups: groups.length,
        proxies: proxies.length
      });
    } catch (error) {
      console.error('Failed to fetch counts:', error);
    }
  };

  const menuItems = [
    { id: 'profiles', icon: Users, label: 'Profiles', count: counts.profiles },
    { id: 'groups', icon: Layers, label: 'Groups', count: counts.groups },
    { id: 'proxies', icon: Shield, label: 'Proxies', count: counts.proxies },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'settings', icon: Settings, label: 'Settings' }
  ];

  return (
    <aside className={`${isCollapsed ? 'w-20' : 'w-72'} bg-gradient-to-b from-slate-900 to-slate-800 border-r border-slate-700/50 flex flex-col shadow-2xl transition-all duration-300`}>
      {/* Logo Section */}
      <div className="p-6 border-b border-slate-700/50">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          {isCollapsed ? (
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-gray-400 hover:text-white"
            >
              <Menu size={20} />
            </button>
          ) : (
            <>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Globe className="text-white" size={24} />
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                    WebProxy
                  </h1>
                  <p className="text-xs text-gray-400">Browser Manager</p>
                </div>
              </div>
              <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-gray-400 hover:text-white"
              >
                <X size={20} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-grow p-4 space-y-2">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={index}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} p-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 text-white shadow-lg'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700/50'
              }`}
              title={isCollapsed ? item.label : ''}
            >
              <div className={`flex items-center ${isCollapsed ? '' : 'space-x-3'}`}>
                <div className={`p-2 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg' 
                    : 'bg-slate-700/50 group-hover:bg-slate-600'
                }`}>
                  <Icon size={18} />
                </div>
                {!isCollapsed && <span className="font-medium">{item.label}</span>}
              </div>
              {!isCollapsed && item.count && (
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  isActive
                    ? 'bg-blue-500/30 text-blue-300'
                    : 'bg-slate-700 text-gray-300'
                }`}>
                  {item.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* User Section */}
      {!isCollapsed && (
        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center space-x-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
              U
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-white">User</p>
              <p className="text-xs text-gray-400">Free Plan</p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;