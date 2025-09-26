import React, { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import EnhancedBadge from './EnhancedBadge';

const BulkOperationsModal = ({ isOpen, onClose, onBulkCreate, onBulkDelete, profiles }) => {
  const [activeTab, setActiveTab] = useState('create');
  const [createData, setCreateData] = useState({
    count: 5,
    deviceType: 'ios',
    prefix: 'Profile',
    enhancedMode: true
  });
  const [selectedProfiles, setSelectedProfiles] = useState([]);

  const deviceTypes = [
    { value: 'ios', label: 'iOS Devices (iPhone/iPad)' },
    { value: 'android', label: 'Android Devices' },
    { value: 'windows', label: 'Windows Desktop' },
    { value: 'macos', label: 'macOS Desktop' },
    { value: 'random', label: 'Random Mix' }
  ];

  const handleBulkCreate = () => {
    onBulkCreate(createData.count, createData.deviceType, createData.prefix, createData.enhancedMode);
    onClose();
  };

  const handleBulkDelete = () => {
    if (selectedProfiles.length === 0) {
      alert('Please select profiles to delete');
      return;
    }
    if (window.confirm(`Delete ${selectedProfiles.length} profiles?`)) {
      onBulkDelete(selectedProfiles);
      setSelectedProfiles([]);
      onClose();
    }
  };

  const toggleProfile = (profileName) => {
    setSelectedProfiles(prev => 
      prev.includes(profileName) 
        ? prev.filter(name => name !== profileName)
        : [...prev, profileName]
    );
  };

  const selectAll = () => {
    setSelectedProfiles(Object.keys(profiles));
  };

  const clearSelection = () => {
    setSelectedProfiles([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-[#1e2024] rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto text-gray-200">
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">Bulk Operations</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setActiveTab('create')}
              className={`px-4 py-2 rounded-lg ${activeTab === 'create' ? 'bg-blue-600' : 'bg-gray-600'}`}
            >
              <Plus size={16} className="inline mr-2" />
              Bulk Create
            </button>
            <button
              onClick={() => setActiveTab('delete')}
              className={`px-4 py-2 rounded-lg ${activeTab === 'delete' ? 'bg-red-600' : 'bg-gray-600'}`}
            >
              <Trash2 size={16} className="inline mr-2" />
              Bulk Delete
            </button>
          </div>

          {activeTab === 'create' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Number of Profiles
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={createData.count}
                  onChange={(e) => setCreateData(prev => ({ ...prev, count: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Device Type
                </label>
                <select
                  value={createData.deviceType}
                  onChange={(e) => setCreateData(prev => ({ ...prev, deviceType: e.target.value }))}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {deviceTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Name Prefix
                </label>
                <input
                  type="text"
                  value={createData.prefix}
                  onChange={(e) => setCreateData(prev => ({ ...prev, prefix: e.target.value }))}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Profiles will be named: {createData.prefix}_1, {createData.prefix}_2, etc.
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Enhanced Mode
                </label>
                <div className="flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setCreateData(prev => ({ ...prev, enhancedMode: !prev.enhancedMode }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      createData.enhancedMode ? 'bg-blue-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        createData.enhancedMode ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm text-gray-300">
                    {createData.enhancedMode ? 'Enhanced Anti-Detection (Recommended)' : 'Standard Mode'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enhanced mode uses advanced anti-detection measures to avoid CAPTCHA issues
                </p>
              </div>
              
              <button
                onClick={handleBulkCreate}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
              >
                Create {createData.count} {createData.enhancedMode ? 'Enhanced' : 'Standard'} Profiles
              </button>
            </div>
          )}

          {activeTab === 'delete' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">
                  Selected: {selectedProfiles.length} / {Object.keys(profiles).length}
                </span>
                <div className="space-x-2">
                  <button
                    onClick={selectAll}
                    className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
                  >
                    Select All
                  </button>
                  <button
                    onClick={clearSelection}
                    className="px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
                  >
                    Clear
                  </button>
                </div>
              </div>
              
              <div className="max-h-60 overflow-y-auto border border-gray-600 rounded-lg">
                {Object.keys(profiles).map(profileName => (
                  <label key={profileName} className="flex items-center p-3 hover:bg-gray-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedProfiles.includes(profileName)}
                      onChange={() => toggleProfile(profileName)}
                      className="mr-3"
                    />
                    <div className="flex-1 flex items-center space-x-2">
                      <span>{profileName}</span>
                      {profiles[profileName].enhancedMode && <EnhancedBadge />}
                    </div>
                    <span className="text-xs text-gray-500">
                      {profiles[profileName].proxy ? 'With Proxy' : 'No Proxy'}
                    </span>
                  </label>
                ))}
              </div>
              
              <button
                onClick={handleBulkDelete}
                disabled={selectedProfiles.length === 0}
                className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition"
              >
                Delete {selectedProfiles.length} Profiles
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BulkOperationsModal;