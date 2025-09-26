import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, Globe, Users, Activity } from 'lucide-react';

const API_URL = 'http://localhost:4000/api';

const Analytics = () => {
  const [analytics, setAnalytics] = useState({ sessions: [], stats: {} });

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${API_URL}/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  const stats = [
    { label: 'Total Sessions', value: analytics.stats.totalSessions || '0', change: '+12%', icon: Activity, color: 'blue' },
    { label: 'Active Profiles', value: analytics.stats.activeProfiles || '0', change: '+5%', icon: Users, color: 'green' },
    { label: 'Avg Session Time', value: analytics.stats.avgSessionTime || '0m', change: '+8%', icon: Clock, color: 'purple' },
    { label: 'Countries', value: analytics.stats.countries || '0', change: '+2', icon: Globe, color: 'orange' }
  ];

  const recentActivity = analytics.sessions.slice(-4).reverse() || [];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Analytics Dashboard</h1>
        <p className="text-gray-400 mt-1">Monitor your browser profile usage and performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const colorClasses = {
            blue: 'from-blue-500 to-blue-600 bg-blue-500/20 text-blue-400',
            green: 'from-green-500 to-green-600 bg-green-500/20 text-green-400',
            purple: 'from-purple-500 to-purple-600 bg-purple-500/20 text-purple-400',
            orange: 'from-orange-500 to-orange-600 bg-orange-500/20 text-orange-400'
          };
          
          return (
            <div key={index} className="bg-gradient-to-br from-slate-800 to-slate-700 p-6 rounded-2xl border border-slate-600/50 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[stat.color].split(' ').slice(2).join(' ')}`}>
                  <Icon size={24} />
                </div>
                <span className="text-green-400 text-sm font-medium">{stat.change}</span>
              </div>
              <div>
                <p className="text-2xl font-bold text-white mb-1">{stat.value}</p>
                <p className="text-gray-400 text-sm">{stat.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Usage Chart */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Usage Overview</h2>
            <BarChart3 className="text-gray-400" size={24} />
          </div>
          <div className="space-y-4">
            {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, index) => {
              const usage = Math.floor(Math.random() * 100);
              return (
                <div key={day} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm w-20">{day}</span>
                  <div className="flex-1 mx-4">
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${usage}%` }}
                      ></div>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm w-12 text-right">{usage}%</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
            <TrendingUp className="text-gray-400" size={24} />
          </div>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-4 p-3 rounded-lg hover:bg-slate-700/30 transition-colors">
                <div className={`w-3 h-3 rounded-full ${
                  activity.status === 'success' ? 'bg-green-400' :
                  activity.status === 'warning' ? 'bg-yellow-400' :
                  'bg-blue-400'
                }`}></div>
                <div className="flex-1">
                  <p className="text-white text-sm font-medium">{activity.profile}</p>
                  <p className="text-gray-400 text-xs">{activity.action}</p>
                </div>
                <span className="text-gray-500 text-xs">{activity.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Browser Distribution */}
      <div className="mt-8 bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
        <h2 className="text-xl font-semibold text-white mb-6">Browser Distribution</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { browser: 'Chrome', percentage: 65, color: 'from-blue-500 to-blue-600' },
            { browser: 'Firefox', percentage: 25, color: 'from-orange-500 to-orange-600' },
            { browser: 'Safari', percentage: 10, color: 'from-gray-500 to-gray-600' }
          ].map((item, index) => (
            <div key={index} className="text-center">
              <div className="relative w-24 h-24 mx-auto mb-4">
                <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="rgb(51 65 85)"
                    strokeWidth="2"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="url(#gradient)"
                    strokeWidth="2"
                    strokeDasharray={`${item.percentage}, 100`}
                  />
                  <defs>
                    <linearGradient id="gradient" className={`bg-gradient-to-r ${item.color}`}>
                      <stop offset="0%" stopColor="#3B82F6" />
                      <stop offset="100%" stopColor="#1D4ED8" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">{item.percentage}%</span>
                </div>
              </div>
              <p className="text-gray-300 font-medium">{item.browser}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;