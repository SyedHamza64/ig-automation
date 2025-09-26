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
  
  // Phase 1 Anti-Detection Features
  const [antiDetection, setAntiDetection] = useState({
    dynamic_user_agent: false,
    enhanced_canvas_fingerprinting: false,
    realistic_device_metrics: false,
    hardware_randomization: false,
    advanced_navigator_properties: false
  });

  const deviceTypes = [
    { value: 'ios', label: 'iOS Devices (iPhone/iPad)' },
    { value: 'android', label: 'Android Devices' },
    { value: 'windows', label: 'Windows Desktop' },
    { value: 'macos', label: 'macOS Desktop' },
    { value: 'random', label: 'Random Mix' }
  ];

  const handleBulkCreate = () => {
    onBulkCreate(createData.count, createData.deviceType, createData.prefix, createData.enhancedMode, antiDetection);
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
              
              {/* Phase 1 Anti-Detection Features */}
              {createData.enhancedMode && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-300">Advanced Anti-Detection Features</h3>
                  <p className="text-sm text-gray-400">
                    Configure specific anti-detection features. All features are disabled by default for backward compatibility.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Dynamic User Agent Generation */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-300">
                          Dynamic User Agent Generation
                        </label>
                        <button
                          type="button"
                          onClick={() => setAntiDetection(prev => ({ ...prev, dynamic_user_agent: !prev.dynamic_user_agent }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            antiDetection.dynamic_user_agent ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              antiDetection.dynamic_user_agent ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400">
                        Generate realistic user agents for different browsers and devices
                      </p>
                    </div>

                    {/* Enhanced Canvas Fingerprinting */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-300">
                          Enhanced Canvas Fingerprinting
                        </label>
                        <button
                          type="button"
                          onClick={() => setAntiDetection(prev => ({ ...prev, enhanced_canvas_fingerprinting: !prev.enhanced_canvas_fingerprinting }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            antiDetection.enhanced_canvas_fingerprinting ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              antiDetection.enhanced_canvas_fingerprinting ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400">
                        Advanced canvas noise with WebGL and font rendering variations
                      </p>
                    </div>

                    {/* Realistic Device Metrics */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-300">
                          Realistic Device Metrics
                        </label>
                        <button
                          type="button"
                          onClick={() => setAntiDetection(prev => ({ ...prev, realistic_device_metrics: !prev.realistic_device_metrics }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            antiDetection.realistic_device_metrics ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              antiDetection.realistic_device_metrics ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400">
                        Use realistic screen resolutions and device scaling factors
                      </p>
                    </div>

                    {/* Hardware Randomization */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-300">
                          Hardware Randomization
                        </label>
                        <button
                          type="button"
                          onClick={() => setAntiDetection(prev => ({ ...prev, hardware_randomization: !prev.hardware_randomization }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            antiDetection.hardware_randomization ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              antiDetection.hardware_randomization ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400">
                        Randomize CPU cores, memory, and platform detection
                      </p>
                    </div>

                    {/* Advanced Navigator Properties */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-600 md:col-span-2">
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm font-medium text-gray-300">
                          Advanced Navigator Properties
                        </label>
                        <button
                          type="button"
                          onClick={() => setAntiDetection(prev => ({ ...prev, advanced_navigator_properties: !prev.advanced_navigator_properties }))}
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                            antiDetection.advanced_navigator_properties ? 'bg-blue-600' : 'bg-gray-600'
                          }`}
                        >
                          <span
                            className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                              antiDetection.advanced_navigator_properties ? 'translate-x-5' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                      <p className="text-xs text-gray-400">
                        Simulate network connection, battery API, media devices, and permissions
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
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