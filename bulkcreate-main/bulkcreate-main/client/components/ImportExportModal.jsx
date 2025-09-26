import React, { useState } from 'react';
import { X, Download, Upload } from 'lucide-react';

const ImportExportModal = ({ isOpen, onClose, onImport }) => {
  const [activeTab, setActiveTab] = useState('export');
  const [importFile, setImportFile] = useState(null);
  const [overwrite, setOverwrite] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleExport = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('http://localhost:4000/api/profiles/export');
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `profiles_export_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('Profiles with data exported successfully!');
    } catch (error) {
      alert('Failed to export profiles: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleImport = async () => {
    if (!importFile) {
      alert('Please select a file to import');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('overwrite', overwrite.toString());
      
      const response = await fetch('http://localhost:4000/api/profiles/import', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Import failed');
      }

      alert('Profiles with data imported successfully!');
      onImport();
      onClose();
    } catch (error) {
      alert('Failed to import profiles: ' + error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'application/zip' || file.name.endsWith('.zip'))) {
      setImportFile(file);
    } else {
      alert('Please select a valid ZIP file');
      e.target.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-[#1e2024] rounded-lg shadow-xl w-full max-w-md text-gray-200">
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">Import / Export Profiles</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-lg">
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setActiveTab('export')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${activeTab === 'export' ? 'bg-green-600' : 'bg-gray-600'}`}
            >
              <Download size={16} />
              <span>Export</span>
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${activeTab === 'import' ? 'bg-blue-600' : 'bg-gray-600'}`}
            >
              <Upload size={16} />
              <span>Import</span>
            </button>
          </div>

          {activeTab === 'export' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Export all your profiles with browser data (cookies, history, passwords) to a ZIP file.
              </p>
              <button
                onClick={handleExport}
                disabled={isProcessing}
                className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition flex items-center justify-center space-x-2"
              >
                <Download size={16} />
                <span>{isProcessing ? 'Exporting...' : 'Export Profiles + Data'}</span>
              </button>
            </div>
          )}

          {activeTab === 'import' && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm">
                Import profiles with all browser data from a previously exported ZIP file.
              </p>
              
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Select ZIP File
                </label>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 bg-[#2d3035] border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="overwrite"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="overwrite" className="text-sm text-gray-400">
                  Overwrite existing profiles with same names
                </label>
              </div>

              <button
                onClick={handleImport}
                disabled={isProcessing || !importFile}
                className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition flex items-center justify-center space-x-2"
              >
                <Upload size={16} />
                <span>{isProcessing ? 'Importing...' : 'Import Profiles + Data'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportExportModal;