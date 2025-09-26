import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';

const CreateProfileModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    remark: '',
    proxy: '',
    user_agent: '',
    language: 'en-US,en;q=0.9',
    timezone: 'Europe/Berlin',
    window_size: [1920, 1080],
    webrtc: 'disabled',
    startup_urls: ['https://httpbin.org/ip'],
    groupId: ''
  });
  const [groups, setGroups] = useState([]);
  const [proxies, setProxies] = useState([]);
  const [useCustomProxy, setUseCustomProxy] = useState(false);
  const [enhancedMode, setEnhancedMode] = useState(true); // Default to enhanced mode
  
  // Phase 1 Anti-Detection Features
  const [antiDetection, setAntiDetection] = useState({
    dynamic_user_agent: false,
    enhanced_canvas_fingerprinting: false,
    realistic_device_metrics: false,
    hardware_randomization: false,
    advanced_navigator_properties: false
  });

  useEffect(() => {
    if (isOpen) {
      fetchGroups();
      fetchProxies();
    }
  }, [isOpen]);

  const fetchGroups = async () => {
    try {
      const response = await fetch('http://localhost:4000/api/groups');
      const data = await response.json();
      setGroups(data);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    }
  };

  const fetchProxies = async () => {
    try {
      const response = await fetch('http://localhost:4000/api/proxies');
      const data = await response.json();
      setProxies(data.filter(p => p.status === 'active'));
    } catch (error) {
      console.error('Failed to fetch proxies:', error);
    }
  };

  const formatProxyUrl = (proxy) => {
    const auth = proxy.username && proxy.password ? `${proxy.username}:${proxy.password}@` : '';
    const protocol = proxy.type.toLowerCase();
    return `${protocol}://${auth}${proxy.host}:${proxy.port}`;
  };

  const userAgents = [
    // Windows Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    // macOS Chrome
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    // Linux Chrome
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    // Windows Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0',
    // macOS Firefox
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0',
    // macOS Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    // Android Chrome
    'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 11; OnePlus 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    // iOS Safari
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    // Android Firefox
    'Mozilla/5.0 (Mobile; rv:127.0) Gecko/127.0 Firefox/127.0',
    'Mozilla/5.0 (Android 13; Mobile; rv:126.0) Gecko/126.0 Firefox/126.0',
    'Mozilla/5.0 (Android 12; Mobile; rv:125.0) Gecko/125.0 Firefox/125.0'
  ];

  const languages = [
    { value: 'en-US,en;q=0.9', label: 'English (US)' },
    { value: 'en-GB,en;q=0.9', label: 'English (UK)' },
    { value: 'es-ES,es;q=0.9', label: 'Spanish' },
    { value: 'fr-FR,fr;q=0.9', label: 'French' },
    { value: 'de-DE,de;q=0.9', label: 'German' },
    { value: 'zh-CN,zh;q=0.9', label: 'Chinese (Simplified)' }
  ];

  const timezones = [
    { value: 'Europe/Berlin', label: 'Berlin (Germany)' },
    { value: 'Europe/Munich', label: 'Munich (Germany)' },
    { value: 'Europe/Hamburg', label: 'Hamburg (Germany)' },
    { value: 'Europe/Cologne', label: 'Cologne (Germany)' },
    { value: 'Europe/Frankfurt', label: 'Frankfurt (Germany)' },
    { value: 'Europe/Stuttgart', label: 'Stuttgart (Germany)' },
    { value: 'Europe/Dusseldorf', label: 'Düsseldorf (Germany)' },
    { value: 'Europe/Vienna', label: 'Vienna (Austria)' },
    { value: 'Europe/Zurich', label: 'Zurich (Switzerland)' },
    { value: 'Europe/Amsterdam', label: 'Amsterdam (Netherlands)' },
    { value: 'Europe/Paris', label: 'Paris (France)' },
    { value: 'Europe/London', label: 'London (UK)' },
    { value: 'Europe/Rome', label: 'Rome (Italy)' },
    { value: 'Europe/Madrid', label: 'Madrid (Spain)' }
  ];

  const screenResolutions = [
    // Desktop resolutions
    [1920, 1080], [1366, 768], [1536, 864], [1440, 900], [1280, 720],
    // Mobile resolutions
    [375, 667], [414, 896], [390, 844], [360, 640], [412, 915]
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleUrlChange = (index, value) => {
    const newUrls = [...formData.startup_urls];
    newUrls[index] = value;
    setFormData(prev => ({ ...prev, startup_urls: newUrls }));
  };

  const addUrl = () => {
    setFormData(prev => ({
      ...prev,
      startup_urls: [...prev.startup_urls, '']
    }));
  };

  const removeUrl = (index) => {
    if (formData.startup_urls.length > 1) {
      const newUrls = formData.startup_urls.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, startup_urls: newUrls }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert('Profile name is required');
      return;
    }
    
    // Filter out empty URLs
    const cleanedUrls = formData.startup_urls.filter(url => url.trim());
    const config = {
      ...formData,
      startup_urls: cleanedUrls.length > 0 ? cleanedUrls : ['https://www.google.com']
    };
    
    onSubmit(formData.name, config, formData.groupId, enhancedMode, antiDetection);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      remark: '',
      proxy: '',
      user_agent: '',
      language: 'en-US,en;q=0.9',
      timezone: 'Europe/Berlin',
      window_size: [1920, 1080],
      webrtc: 'disabled',
      startup_urls: ['https://www.google.com'],
      groupId: ''
    });
    setEnhancedMode(true); // Reset to enhanced mode
    setUseCustomProxy(false);
    setAntiDetection({
      dynamic_user_agent: false,
      enhanced_canvas_fingerprinting: false,
      realistic_device_metrics: false,
      hardware_randomization: false,
      advanced_navigator_properties: false
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-[#1e2024] rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto text-gray-200">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">Create New Profile</h2>
          <button onClick={handleClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Profile Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Group
              </label>
              <select
                value={formData.groupId}
                onChange={(e) => handleInputChange('groupId', e.target.value)}
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No Group</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Remark
              </label>
              <input
                type="text"
                value={formData.remark}
                onChange={(e) => handleInputChange('remark', e.target.value)}
                placeholder="Optional description"
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Proxy Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300">Proxy Settings</h3>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="proxyType"
                  checked={!useCustomProxy}
                  onChange={() => {
                    setUseCustomProxy(false);
                    handleInputChange('proxy', '');
                  }}
                  className="text-blue-600"
                />
                <span className="text-gray-300">Select from saved proxies</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="proxyType"
                  checked={useCustomProxy}
                  onChange={() => setUseCustomProxy(true)}
                  className="text-blue-600"
                />
                <span className="text-gray-300">Custom proxy</span>
              </label>
            </div>

            {!useCustomProxy ? (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Select Proxy
                </label>
                <select
                  value={formData.proxy}
                  onChange={(e) => handleInputChange('proxy', e.target.value)}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No Proxy</option>
                  {proxies.map((proxy) => (
                    <option key={proxy.id} value={formatProxyUrl(proxy)}>
                      {proxy.name} ({proxy.type}) - {proxy.host}:{proxy.port}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Custom Proxy URL
                </label>
                <input
                  type="text"
                  value={formData.proxy}
                  onChange={(e) => handleInputChange('proxy', e.target.value)}
                  placeholder="http://user:pass@host:port or socks5://user:pass@host:port"
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Supports: HTTP, HTTPS, SOCKS5 with username:password authentication
                </p>
              </div>
            )}
          </div>

          {/* Browser Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300">Browser Settings</h3>
            
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                User Agent
              </label>
              <select
                value={formData.user_agent}
                onChange={(e) => handleInputChange('user_agent', e.target.value)}
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Random (Recommended)</option>
                {userAgents.map((ua, index) => {
                  let browser = 'Unknown';
                  let platform = 'Unknown';
                  
                  if (ua.includes('Chrome') && ua.includes('Mobile')) browser = 'Chrome Mobile';
                  else if (ua.includes('Chrome')) browser = 'Chrome';
                  else if (ua.includes('Firefox') && ua.includes('Mobile')) browser = 'Firefox Mobile';
                  else if (ua.includes('Firefox')) browser = 'Firefox';
                  else if (ua.includes('Safari') && ua.includes('Mobile')) browser = 'Safari Mobile';
                  else if (ua.includes('Safari')) browser = 'Safari';
                  
                  if (ua.includes('Windows')) platform = 'Windows';
                  else if (ua.includes('Macintosh') || ua.includes('Mac OS X')) platform = 'macOS';
                  else if (ua.includes('Linux') && !ua.includes('Android')) platform = 'Linux';
                  else if (ua.includes('Android')) platform = 'Android';
                  else if (ua.includes('iPhone')) platform = 'iPhone';
                  else if (ua.includes('iPad')) platform = 'iPad';
                  
                  return (
                    <option key={index} value={ua}>
                      {browser} - {platform}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Language
                </label>
                <select
                  value={formData.language}
                  onChange={(e) => handleInputChange('language', e.target.value)}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {languages.map((lang) => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Timezone
                </label>
                <select
                  value={formData.timezone}
                  onChange={(e) => handleInputChange('timezone', e.target.value)}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {timezones.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Fingerprint Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300">Fingerprint Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Screen Resolution
                </label>
                <select
                  value={JSON.stringify(formData.window_size)}
                  onChange={(e) => handleInputChange('window_size', JSON.parse(e.target.value))}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {screenResolutions.map((res) => (
                    <option key={`${res[0]}x${res[1]}`} value={JSON.stringify(res)}>
                      {res[0]} x {res[1]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  WebRTC
                </label>
                <select
                  value={formData.webrtc}
                  onChange={(e) => handleInputChange('webrtc', e.target.value)}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="disabled">Disabled</option>
                  <option value="replace">Replace</option>
                  <option value="real">Real</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Enhanced Mode
                </label>
                <div className="flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setEnhancedMode(!enhancedMode)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      enhancedMode ? 'bg-blue-600' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        enhancedMode ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className="text-sm text-gray-300">
                    {enhancedMode ? 'Enhanced Anti-Detection (Recommended)' : 'Standard Mode'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enhanced mode uses advanced anti-detection measures to avoid CAPTCHA issues
                </p>
              </div>
            </div>
          </div>

          {/* Phase 1 Anti-Detection Features */}
          {enhancedMode && (
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

          {/* Startup URLs */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-300">Startup URLs</h3>
              <button
                type="button"
                onClick={addUrl}
                className="flex items-center space-x-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-md text-sm"
              >
                <Plus size={16} />
                <span>Add URL</span>
              </button>
            </div>
            
            <div className="space-y-2">
              {formData.startup_urls.map((url, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => handleUrlChange(index, e.target.value)}
                    placeholder="https://example.com"
                    className="flex-1 px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {formData.startup_urls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeUrl(index)}
                      className="p-2 text-red-400 hover:bg-red-500 hover:text-white rounded-md"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              className="px-6 py-2 rounded-md bg-gray-600 hover:bg-gray-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 rounded-md bg-blue-600 hover:bg-blue-700 transition"
            >
              Create Profile
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProfileModal;