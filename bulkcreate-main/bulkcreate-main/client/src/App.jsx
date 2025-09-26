// src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MoreVertical, Plus, Eye } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import CreateProfileModal from '../components/CreateProfileModal';
import ProfileDetailsModal from '../components/ProfileDetailsModal';
import BulkOperationsModal from '../components/BulkOperationsModal';
import ImportExportModal from '../components/ImportExportModal';
import ChangeProxyModal from '../components/ChangeProxyModal';
import EnhancedBadge from '../components/EnhancedBadge';
import Groups from '../components/Groups';
import Proxies from '../components/Proxies';
import Analytics from '../components/Analytics';
import Settings from '../components/Settings';

const API_URL = 'http://localhost:4000/api';

function App() {
  const [profiles, setProfiles] = useState({});
  const [profileStatus, setProfileStatus] = useState({});
  const [activeMenu, setActiveMenu] = useState(null);
  const menuRef = useRef(null);

  // --- STATE FOR THE MODALS ---
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [isImportExportModalOpen, setIsImportExportModalOpen] = useState(false);
  const [isChangeProxyModalOpen, setIsChangeProxyModalOpen] = useState(false);
  const [selectedProfileForProxy, setSelectedProfileForProxy] = useState(null);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [selectedProfileName, setSelectedProfileName] = useState('');
  const [currentPage, setCurrentPage] = useState('profiles');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sidebarKey, setSidebarKey] = useState(0);

  const fetchProfiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/profiles`);
      const data = await response.json();
      setProfiles(data);
    } catch (error) {
      console.error("Failed to fetch profiles:", error);
    }
  }, []);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  useEffect(() => {
    const fetchStatus = async () => {
      if (Object.keys(profiles).length === 0) return;
      try {
        const response = await fetch(`${API_URL}/status`);
        const runningProfiles = await response.json();
        const newStatus = {};
        Object.keys(profiles).forEach(name => {
          newStatus[name] = runningProfiles.includes(name) ? 'running' : 'stopped';
        });
        setProfileStatus(prevStatus => ({ ...prevStatus, ...newStatus }));
      } catch (error) {
        console.error("Failed to fetch status:", error);
      }
    };
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [profiles]);
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setActiveMenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleCreate = async (name, config, groupId, enhancedMode = true, antiDetection = {}) => {
    try {
      const response = await fetch(`${API_URL}/profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, config, enhancedMode, antiDetection }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to create profile: ${errorData.error}`);
        return;
      }
      setIsModalOpen(false);
      fetchProfiles();
      setSidebarKey(prev => prev + 1);
    } catch (error) {
      console.error("Failed to create profile:", error);
      alert("Failed to create profile. Check console for details.");
    }
  };

  const handleViewDetails = (name, config) => {
    setSelectedProfile(config);
    setSelectedProfileName(name);
    setIsDetailsModalOpen(true);
    setActiveMenu(null);
  };
  
  const handleDelete = async (name) => {
    if (window.confirm(`Are you sure you want to delete profile "${name}"?`)) {
      try {
        const response = await fetch(`${API_URL}/profiles/delete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name }),
        });
        if (!response.ok) {
          const errorData = await response.json();
          alert(`Failed to delete profile: ${errorData.error}`);
          return;
        }
        setActiveMenu(null);
        fetchProfiles();
        setSidebarKey(prev => prev + 1);
      } catch (error) {
        console.error("Failed to delete profile:", error);
        alert("Failed to delete profile. Check console for details.");
      }
    }
  };

  const handleBulkCreate = async (count, deviceType, prefix, enhancedMode = true, antiDetection = {}) => {
    try {
      const response = await fetch(`${API_URL}/profiles/bulk-create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count, deviceType, prefix, enhancedMode, antiDetection }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to create profiles: ${errorData.error}`);
        return;
      }
      fetchProfiles();
      setSidebarKey(prev => prev + 1);
    } catch (error) {
      console.error("Failed to create profiles:", error);
      alert("Failed to create profiles. Check console for details.");
    }
  };

  const handleBulkDelete = async (names) => {
    try {
      const response = await fetch(`${API_URL}/profiles/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ names }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to delete profiles: ${errorData.error}`);
        return;
      }
      fetchProfiles();
      setSidebarKey(prev => prev + 1);
    } catch (error) {
      console.error("Failed to delete profiles:", error);
      alert("Failed to delete profiles. Check console for details.");
    }
  };

  const handleDisableProxy = async (name) => {
    try {
      const response = await fetch(`${API_URL}/profiles/disable-proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to disable proxy: ${errorData.error}`);
        return;
      }
      setActiveMenu(null);
      fetchProfiles();
    } catch (error) {
      console.error("Failed to disable proxy:", error);
      alert("Failed to disable proxy. Check console for details.");
    }
  };

  const handleRename = async (oldName) => {
    const newName = prompt(`Enter new name for profile "${oldName}":`, oldName);
    if (!newName || newName === oldName) return;
    
    try {
      const response = await fetch(`${API_URL}/profiles/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ oldName, newName }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to rename profile: ${errorData.error}`);
        return;
      }
      setActiveMenu(null);
      fetchProfiles();
      setSidebarKey(prev => prev + 1);
    } catch (error) {
      console.error("Failed to rename profile:", error);
      alert("Failed to rename profile. Check console for details.");
    }
  };

  const handleChangeProxy = (name, config) => {
    setSelectedProfileForProxy({ name, config });
    setIsChangeProxyModalOpen(true);
    setActiveMenu(null);
  };

  const handleProxyChange = async (newProxy) => {
    try {
      const response = await fetch(`${API_URL}/profiles/change-proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: selectedProfileForProxy.name, proxy: newProxy }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        alert(`Failed to change proxy: ${errorData.error}`);
        return;
      }
      fetchProfiles();
    } catch (error) {
      console.error("Failed to change proxy:", error);
      alert("Failed to change proxy. Check console for details.");
    }
  };

  const handleLaunch = async (name) => {
    setProfileStatus(prev => ({ ...prev, [name]: 'opening' }));
    await fetch(`${API_URL}/profiles/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
  };

  const handleClose = async (name) => {
    setProfileStatus(prev => ({ ...prev, [name]: 'closing' }));
    await fetch(`${API_URL}/profiles/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
  };

  const getButton = (name) => {
    const status = profileStatus[name];
    if (status === 'opening') return <button className="px-4 py-2 rounded-lg text-sm bg-gradient-to-r from-yellow-500 to-orange-500 text-white cursor-not-allowed shadow-lg">Opening...</button>;
    if (status === 'closing') return <button className="px-4 py-2 rounded-lg text-sm bg-gradient-to-r from-gray-500 to-gray-600 text-white cursor-not-allowed shadow-lg">Closing...</button>;
    if (status === 'running') return <button onClick={() => handleClose(name)} className="px-4 py-2 rounded-lg text-sm bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg transition-all duration-200 transform hover:scale-105">Close</button>;
    return <button onClick={() => handleLaunch(name)} className="px-4 py-2 rounded-lg text-sm bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white shadow-lg transition-all duration-200 transform hover:scale-105">Launch</button>;
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'groups':
        return <Groups />;
      case 'proxies':
        return <Proxies />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <Settings />;
      default:
        return renderProfilesPage();
    }
  };

  const renderProfilesPage = () => (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Browser Profiles</h1>
          <p className="text-gray-400 mt-1">Manage your browser fingerprints and sessions</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          >
            <Plus size={20} />
            <span>Create Profile</span>
          </button>
          <button
            onClick={() => setIsBulkModalOpen(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white font-medium px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
            </svg>
            <span>Bulk Operations</span>
          </button>
          <button
            onClick={() => setIsImportExportModalOpen(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-medium px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" />
            </svg>
            <span>Import/Export</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 p-6 rounded-2xl border border-slate-600/50 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm font-medium">Total Profiles</p>
              <p className="text-2xl font-bold text-white">{Object.keys(profiles).length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
              <Plus className="text-blue-400" size={24} />
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 p-6 rounded-2xl border border-slate-600/50 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm font-medium">Active Sessions</p>
              <p className="text-2xl font-bold text-green-400">{Object.values(profileStatus).filter(s => s === 'running').length}</p>
            </div>
            <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-slate-800 to-slate-700 p-6 rounded-2xl border border-slate-600/50 shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm font-medium">With Proxy</p>
              <p className="text-2xl font-bold text-purple-400">{Object.values(profiles).filter(p => p.proxy).length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-purple-400 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 overflow-visible">
        <div className="p-6 border-b border-slate-600/50">
          <h2 className="text-xl font-semibold text-white">Profile Management</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Profile</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Proxy</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Browser</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Remark</th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-600/50">
              {Object.entries(profiles).map(([name, config]) => (
                <tr key={name} className="hover:bg-slate-700/30 transition-all duration-200">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-sm mr-3">
                        {name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-white">{name}</span>
                          {config.enhancedMode && <EnhancedBadge />}
                        </div>
                        <div className="text-xs text-gray-400">{new Date().toLocaleDateString()}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      profileStatus[name] === 'running' ? 'bg-green-100 text-green-800' :
                      profileStatus[name] === 'opening' ? 'bg-yellow-100 text-yellow-800' :
                      profileStatus[name] === 'closing' ? 'bg-orange-100 text-orange-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                        profileStatus[name] === 'running' ? 'bg-green-400 animate-pulse' :
                        profileStatus[name] === 'opening' ? 'bg-yellow-400 animate-pulse' :
                        profileStatus[name] === 'closing' ? 'bg-orange-400 animate-pulse' :
                        'bg-gray-400'
                      }`}></div>
                      {profileStatus[name] || 'stopped'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">
                    {config.proxy ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-md bg-purple-500/20 text-purple-300 text-xs">
                        <div className="w-2 h-2 bg-purple-400 rounded-full mr-1"></div>
                        Enabled
                      </span>
                    ) : (
                      <span className="text-gray-500">None</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300">
                    <span className="inline-flex items-center px-2 py-1 rounded-md bg-blue-500/20 text-blue-300 text-xs">
                      {config.user_agent ? (
                        config.user_agent.includes('iPhone') || config.user_agent.includes('iPad') ? 'iOS Safari' :
                        config.user_agent.includes('Android') && config.user_agent.includes('Chrome') ? 'Android Chrome' :
                        config.user_agent.includes('Android') && config.user_agent.includes('Firefox') ? 'Android Firefox' :
                        config.user_agent.includes('Chrome') ? 'Chrome' :
                        config.user_agent.includes('Firefox') ? 'Firefox' : 'Safari'
                      ) : 'Random'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{config.remark || '-'}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      {getButton(name)}
                      <div className="relative" ref={activeMenu === name ? menuRef : null}>
                        <button
                          data-menu={name}
                          onClick={() => setActiveMenu(activeMenu === name ? null : name)}
                          className="p-2 rounded-lg hover:bg-slate-600/50 transition-colors"
                        >
                          <MoreVertical size={18} className="text-gray-400" />
                        </button>
                        {activeMenu === name && (
                          <div className="fixed w-48 bg-slate-800 border border-slate-600 rounded-xl shadow-2xl z-50 backdrop-blur-sm" style={{
                            right: '2rem',
                            top: `${document.querySelector(`[data-menu="${name}"]`)?.getBoundingClientRect().top - 100}px`
                          }}>
                            <button
                              onClick={() => handleViewDetails(name, config)}
                              className="flex items-center w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-slate-700 transition-colors"
                            >
                              <Eye size={16} className="mr-3" />
                              View Details
                            </button>
                            <button
                              onClick={() => handleRename(name)}
                              className="flex items-center w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-slate-700 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                              </svg>
                              Rename Profile
                            </button>
                            <button
                              onClick={() => handleChangeProxy(name, config)}
                              className="flex items-center w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-slate-700 transition-colors"
                            >
                              <svg className="w-4 h-4 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z" />
                              </svg>
                              Change Proxy
                            </button>
                            {config.proxy && (
                              <button
                                onClick={() => handleDisableProxy(name)}
                                className="flex items-center w-full text-left px-4 py-3 text-sm text-orange-400 hover:bg-orange-500/20 transition-colors"
                              >
                                <svg className="w-4 h-4 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
                                </svg>
                                Disable Proxy
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(name)}
                              className="flex items-center w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-red-500/20 rounded-b-xl transition-colors"
                            >
                              <svg className="w-4 h-4 mr-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9zM4 5a2 2 0 012-2h8a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 112 0v3a1 1 0 11-2 0V9zm4 0a1 1 0 112 0v3a1 1 0 11-2 0V9z" clipRule="evenodd" />
                              </svg>
                              Delete Profile
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="flex h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 text-gray-100">
        <Sidebar 
          key={sidebarKey}
          isCollapsed={isCollapsed} 
          setIsCollapsed={setIsCollapsed}
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
        />
        <main className="flex-1 overflow-auto">
          {renderCurrentPage()}
        </main>
      </div>
      
      <CreateProfileModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreate}
      />
      
      <ProfileDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        profile={selectedProfile}
        profileName={selectedProfileName}
      />
      
      <BulkOperationsModal
        isOpen={isBulkModalOpen}
        onClose={() => setIsBulkModalOpen(false)}
        onBulkCreate={handleBulkCreate}
        onBulkDelete={handleBulkDelete}
        profiles={profiles}
      />
      
      <ImportExportModal
        isOpen={isImportExportModalOpen}
        onClose={() => setIsImportExportModalOpen(false)}
        onImport={() => {
          fetchProfiles();
          setSidebarKey(prev => prev + 1);
        }}
      />
      
      <ChangeProxyModal
        isOpen={isChangeProxyModalOpen}
        onClose={() => setIsChangeProxyModalOpen(false)}
        onSubmit={handleProxyChange}
        profileName={selectedProfileForProxy?.name}
        currentProxy={selectedProfileForProxy?.config?.proxy}
      />
    </>
  );
}

export default App;