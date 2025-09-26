import React, { useState, useEffect } from 'react';
import { Plus, Users, Edit, Trash2, MoreVertical, X } from 'lucide-react';

const API_URL = 'http://localhost:4000/api';

const Groups = () => {
  const [groups, setGroups] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newGroup, setNewGroup] = useState({ name: '', description: '' });
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [groupProfiles, setGroupProfiles] = useState([]);
  const [isAddProfileModalOpen, setIsAddProfileModalOpen] = useState(false);
  const [allProfiles, setAllProfiles] = useState([]);
  const [selectedProfiles, setSelectedProfiles] = useState([]);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await fetch(`${API_URL}/groups`);
      const data = await response.json();
      setGroups(data);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newGroup)
      });
      if (response.ok) {
        setNewGroup({ name: '', description: '' });
        setIsModalOpen(false);
        fetchGroups();
      }
    } catch (error) {
      console.error('Failed to create group:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this group?')) {
      try {
        const response = await fetch(`${API_URL}/groups/${id}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          fetchGroups();
        }
      } catch (error) {
        console.error('Failed to delete group:', error);
      }
    }
  };

  const handleViewProfiles = async (groupId) => {
    setSelectedGroupId(groupId);
    try {
      const response = await fetch(`${API_URL}/groups/${groupId}/profiles`);
      const profiles = await response.json();
      setGroupProfiles(profiles);
      setIsProfileModalOpen(true);
    } catch (error) {
      console.error('Failed to fetch group profiles:', error);
    }
  };

  const handleAddProfile = async (groupId) => {
    setSelectedGroupId(groupId);
    try {
      const response = await fetch(`${API_URL}/profiles`);
      const profiles = await response.json();
      setAllProfiles(Object.keys(profiles));
      setSelectedProfiles([]);
      setIsAddProfileModalOpen(true);
    } catch (error) {
      console.error('Failed to fetch profiles:', error);
    }
  };

  const handleAssignProfiles = async () => {
    try {
      const response = await fetch(`${API_URL}/groups/${selectedGroupId}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profiles: selectedProfiles })
      });
      if (response.ok) {
        setIsAddProfileModalOpen(false);
        fetchGroups();
      }
    } catch (error) {
      console.error('Failed to assign profiles:', error);
    }
  };

  const toggleProfileSelection = (profileName) => {
    setSelectedProfiles(prev => 
      prev.includes(profileName) 
        ? prev.filter(p => p !== profileName)
        : [...prev, profileName]
    );
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Profile Groups</h1>
          <p className="text-gray-400 mt-1">Organize your profiles into groups</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
        >
          <Plus size={20} />
          <span>Create Group</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => (
          <div key={group.id} className="bg-gradient-to-br from-slate-800/80 to-slate-700/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-slate-600/50 p-6">
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                <Users className="text-white" size={24} />
              </div>
              <button className="p-2 rounded-lg hover:bg-slate-600/50 transition-colors">
                <MoreVertical size={18} className="text-gray-400" />
              </button>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">{group.name}</h3>
            <p className="text-gray-400 text-sm mb-4">{group.description}</p>
            <div className="flex justify-between items-center">
              <span className="text-2xl font-bold text-blue-400">{group.profiles}</span>
              <span className="text-gray-400 text-sm">profiles</span>
            </div>
            <div className="flex space-x-2 mt-4">
              <button 
                onClick={() => handleViewProfiles(group.id)}
                className="flex-1 px-3 py-2 bg-blue-600/20 text-blue-300 rounded-lg hover:bg-blue-600/30 transition-colors text-sm"
              >
                View Profiles
              </button>
              <button 
                onClick={() => handleAddProfile(group.id)}
                className="px-3 py-2 bg-green-600/20 text-green-300 rounded-lg hover:bg-green-600/30 transition-colors"
              >
                <Plus size={16} />
              </button>
              <button 
                onClick={() => handleDelete(group.id)}
                className="px-3 py-2 bg-red-600/20 text-red-300 rounded-lg hover:bg-red-600/30 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-slate-800 p-6 rounded-2xl shadow-xl w-full max-w-md border border-slate-600">
            <h2 className="text-xl font-bold text-white mb-4">Create New Group</h2>
            <form onSubmit={handleCreate}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">Group Name</label>
                <input
                  type="text"
                  value={newGroup.name}
                  onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                  required
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                <textarea
                  value={newGroup.description}
                  onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                  rows="3"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isProfileModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-slate-800 p-6 rounded-2xl shadow-xl w-full max-w-2xl border border-slate-600">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Group Profiles</h2>
              <button
                onClick={() => setIsProfileModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {groupProfiles.length > 0 ? (
                <div className="space-y-2">
                  {groupProfiles.map((profile, index) => (
                    <div key={index} className="flex items-center p-3 bg-slate-700 rounded-lg">
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm mr-3">
                        {profile.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-white">{profile}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">No profiles assigned to this group</p>
              )}
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => handleAddProfile(selectedGroupId)}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition"
              >
                Add Profiles
              </button>
            </div>
          </div>
        </div>
      )}

      {isAddProfileModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-slate-800 p-6 rounded-2xl shadow-xl w-full max-w-2xl border border-slate-600">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Add Profiles to Group</h2>
              <button
                onClick={() => setIsAddProfileModalOpen(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>
            <div className="max-h-96 overflow-y-auto mb-4">
              {allProfiles.length > 0 ? (
                <div className="space-y-2">
                  {allProfiles.map((profileName) => (
                    <div key={profileName} className="flex items-center p-3 bg-slate-700 rounded-lg hover:bg-slate-600 cursor-pointer" onClick={() => toggleProfileSelection(profileName)}>
                      <input
                        type="checkbox"
                        checked={selectedProfiles.includes(profileName)}
                        onChange={() => toggleProfileSelection(profileName)}
                        className="mr-3"
                      />
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm mr-3">
                        {profileName.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-white">{profileName}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">No profiles available</p>
              )}
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsAddProfileModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white transition"
              >
                Cancel
              </button>
              <button
                onClick={handleAssignProfiles}
                disabled={selectedProfiles.length === 0}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Assign {selectedProfiles.length} Profile(s)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Groups;