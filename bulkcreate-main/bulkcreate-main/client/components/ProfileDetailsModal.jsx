import React from 'react';
import { X, Globe, Monitor, Clock, Shield, Link } from 'lucide-react';

const ProfileDetailsModal = ({ isOpen, onClose, profile, profileName }) => {
  if (!isOpen || !profile) return null;

  const formatResolution = (windowSize) => {
    if (Array.isArray(windowSize) && windowSize.length === 2) {
      return `${windowSize[0]} x ${windowSize[1]}`;
    }
    return 'Not set';
  };

  const formatUserAgent = (userAgent) => {
    if (!userAgent) return 'Random';
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    return 'Custom';
  };

  const getLanguageLabel = (langCode) => {
    const languages = {
      'en-US,en;q=0.9': 'English (US)',
      'en-GB,en;q=0.9': 'English (UK)',
      'es-ES,es;q=0.9': 'Spanish',
      'fr-FR,fr;q=0.9': 'French',
      'de-DE,de;q=0.9': 'German',
      'zh-CN,zh;q=0.9': 'Chinese (Simplified)'
    };
    return languages[langCode] || langCode;
  };

  const getTimezoneLabel = (timezone) => {
    const timezones = {
      'America/New_York': 'Eastern Time (US)',
      'America/Los_Angeles': 'Pacific Time (US)',
      'Europe/London': 'London',
      'Europe/Paris': 'Paris',
      'Asia/Tokyo': 'Tokyo',
      'Australia/Sydney': 'Sydney'
    };
    return timezones[timezone] || timezone;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-[#1e2024] rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto text-gray-200">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">Profile Details: {profileName}</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300 flex items-center">
              <Globe className="mr-2" size={20} />
              Basic Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#2d3035] p-4 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Profile Name</label>
                <p className="text-gray-200">{profileName}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Remark</label>
                <p className="text-gray-200">{profile.remark || 'No remark'}</p>
              </div>
            </div>
          </div>

          {/* Proxy Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300 flex items-center">
              <Shield className="mr-2" size={20} />
              Proxy Settings
            </h3>
            <div className="bg-[#2d3035] p-4 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Proxy</label>
                <p className="text-gray-200 font-mono text-sm">
                  {profile.proxy || 'No proxy configured'}
                </p>
              </div>
            </div>
          </div>

          {/* Browser Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300 flex items-center">
              <Monitor className="mr-2" size={20} />
              Browser Settings
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-[#2d3035] p-4 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">User Agent</label>
                <p className="text-gray-200">{formatUserAgent(profile.user_agent)}</p>
                {profile.user_agent && (
                  <p className="text-xs text-gray-400 mt-1 break-all">{profile.user_agent}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Language</label>
                <p className="text-gray-200">{getLanguageLabel(profile.language)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Timezone</label>
                <p className="text-gray-200">{getTimezoneLabel(profile.timezone)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Screen Resolution</label>
                <p className="text-gray-200">{formatResolution(profile.window_size)}</p>
              </div>
            </div>
          </div>

          {/* Fingerprint Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300 flex items-center">
              <Clock className="mr-2" size={20} />
              Fingerprint Settings
            </h3>
            <div className="bg-[#2d3035] p-4 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">WebRTC</label>
                <p className="text-gray-200 capitalize">{profile.webrtc || 'disabled'}</p>
              </div>
            </div>
          </div>

          {/* Startup URLs */}
          {profile.startup_urls && profile.startup_urls.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-300 flex items-center">
                <Link className="mr-2" size={20} />
                Startup URLs
              </h3>
              <div className="bg-[#2d3035] p-4 rounded-lg">
                <div className="space-y-2">
                  {profile.startup_urls.map((url, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <span className="text-gray-400 text-sm w-6">{index + 1}.</span>
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline break-all"
                      >
                        {url}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Close Button */}
          <div className="flex justify-end pt-4 border-t border-gray-700">
            <button
              onClick={onClose}
              className="px-6 py-2 rounded-md bg-gray-600 hover:bg-gray-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileDetailsModal;