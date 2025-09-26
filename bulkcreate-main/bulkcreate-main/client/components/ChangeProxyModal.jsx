import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const ChangeProxyModal = ({ isOpen, onClose, onSubmit, profileName, currentProxy }) => {
  const [proxy, setProxy] = useState('');
  const [proxies, setProxies] = useState([]);
  const [useCustomProxy, setUseCustomProxy] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setProxy(currentProxy || '');
      setUseCustomProxy(!!currentProxy && !proxies.some(p => formatProxyUrl(p) === currentProxy));
      fetchProxies();
    }
  }, [isOpen, currentProxy]);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(proxy);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-[#1e2024] rounded-lg shadow-xl w-full max-w-md text-gray-200">
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">Change Proxy</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <p className="text-sm text-gray-400 mb-4">
              Profile: <span className="text-white font-medium">{profileName}</span>
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="radio"
                name="proxyType"
                checked={!useCustomProxy}
                onChange={() => {
                  setUseCustomProxy(false);
                  setProxy('');
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
                value={proxy}
                onChange={(e) => setProxy(e.target.value)}
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No Proxy</option>
                {proxies.map((proxyItem) => (
                  <option key={proxyItem.id} value={formatProxyUrl(proxyItem)}>
                    {proxyItem.name} ({proxyItem.type}) - {proxyItem.host}:{proxyItem.port}
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
                value={proxy}
                onChange={(e) => setProxy(e.target.value)}
                placeholder="http://user:pass@host:port or leave empty to remove proxy"
                className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Leave empty to remove proxy completely
              </p>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 rounded-md bg-gray-600 hover:bg-gray-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 rounded-md bg-blue-600 hover:bg-blue-700 transition"
            >
              Change Proxy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChangeProxyModal;