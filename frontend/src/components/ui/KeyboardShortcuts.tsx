// frontend/src/components/ui/KeyboardShortcuts.tsx

import { useEffect, useState } from "react";

interface KeyboardShortcutsProps {
  onSave: () => void;
  onCancel: () => void;
  onReset: () => void;
  onToggleBulk: () => void;
  onToggleUsage: () => void;
  onToggleTemplates: () => void;
  onExport: () => void;
  onImport: () => void;
  hasChanges: boolean;
  className?: string;
}

interface Shortcut {
  key: string;
  description: string;
  action: () => void;
  condition?: () => boolean;
}

export function KeyboardShortcuts({
  onSave,
  onCancel,
  onReset,
  onToggleBulk,
  onToggleUsage,
  onToggleTemplates,
  onExport,
  onImport,
  hasChanges,
  className = ""
}: KeyboardShortcutsProps) {
  const [showHelp, setShowHelp] = useState(false);

  const shortcuts: Shortcut[] = [
    {
      key: "Ctrl+S",
      description: "Save changes",
      action: onSave,
      condition: () => hasChanges
    },
    {
      key: "Escape",
      description: "Cancel changes",
      action: onCancel,
      condition: () => hasChanges
    },
    {
      key: "Ctrl+R",
      description: "Reset to defaults",
      action: onReset
    },
    {
      key: "Ctrl+B",
      description: "Toggle bulk operations",
      action: onToggleBulk
    },
    {
      key: "Ctrl+U",
      description: "Toggle usage statistics",
      action: onToggleUsage
    },
    {
      key: "Ctrl+T",
      description: "Toggle templates",
      action: onToggleTemplates
    },
    {
      key: "Ctrl+E",
      description: "Export limits",
      action: onExport
    },
    {
      key: "Ctrl+I",
      description: "Import limits",
      action: onImport
    },
    {
      key: "?",
      description: "Show/hide shortcuts",
      action: () => setShowHelp(!showHelp)
    }
  ];

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (event.target instanceof HTMLInputElement || 
          event.target instanceof HTMLTextAreaElement ||
          event.target instanceof HTMLSelectElement) {
        return;
      }

      const key = event.key.toLowerCase();
      const ctrl = event.ctrlKey || event.metaKey;
      const shift = event.shiftKey;
      const alt = event.altKey;

      // Handle shortcuts
      if (ctrl && key === 's') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+S");
        if (shortcut && (!shortcut.condition || shortcut.condition())) {
          shortcut.action();
        }
      } else if (key === 'escape') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Escape");
        if (shortcut && (!shortcut.condition || shortcut.condition())) {
          shortcut.action();
        }
      } else if (ctrl && key === 'r') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+R");
        if (shortcut) shortcut.action();
      } else if (ctrl && key === 'b') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+B");
        if (shortcut) shortcut.action();
      } else if (ctrl && key === 'u') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+U");
        if (shortcut) shortcut.action();
      } else if (ctrl && key === 't') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+T");
        if (shortcut) shortcut.action();
      } else if (ctrl && key === 'e') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+E");
        if (shortcut) shortcut.action();
      } else if (ctrl && key === 'i') {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "Ctrl+I");
        if (shortcut) shortcut.action();
      } else if (key === '?' && !ctrl && !shift && !alt) {
        event.preventDefault();
        const shortcut = shortcuts.find(s => s.key === "?");
        if (shortcut) shortcut.action();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts, hasChanges]);

  return (
    <div className={className}>
      {/* Help Button */}
      <button
        onClick={() => setShowHelp(!showHelp)}
        className="inline-flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
        title="Keyboard shortcuts (?)"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Shortcuts
      </button>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Keyboard Shortcuts
                </h3>
                <button
                  onClick={() => setShowHelp(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-3">
                {shortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className={`flex items-center justify-between p-2 rounded ${
                      shortcut.condition && !shortcut.condition() 
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500' 
                        : 'bg-gray-50 dark:bg-gray-700'
                    }`}
                  >
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {shortcut.description}
                    </span>
                    <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-gray-200 dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>Tip:</strong> Press <kbd className="px-1 py-0.5 text-xs bg-blue-200 dark:bg-blue-800 rounded">?</kbd> anytime to show/hide this help.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



