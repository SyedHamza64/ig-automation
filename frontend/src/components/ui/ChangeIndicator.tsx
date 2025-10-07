// frontend/src/components/ui/ChangeIndicator.tsx


interface ChangeIndicatorProps {
  hasChanges: boolean;
  className?: string;
  showIcon?: boolean;
}

export function ChangeIndicator({ 
  hasChanges, 
  className = "", 
  showIcon = true 
}: ChangeIndicatorProps) {
  if (!hasChanges) return null;

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium bg-orange-50 text-orange-700 border border-orange-200 ${className}`}>
      {showIcon && (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      )}
      <span>Unsaved changes</span>
    </div>
  );
}

interface SaveStatusProps {
  isSaving: boolean;
  lastSaved?: Date;
  className?: string;
}

export function SaveStatus({ 
  isSaving, 
  lastSaved, 
  className = "" 
}: SaveStatusProps) {
  if (isSaving) {
    return (
      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700 border border-blue-200 ${className}`}>
        <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        <span>Saving...</span>
      </div>
    );
  }

  if (lastSaved) {
    return (
      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium bg-green-50 text-green-700 border border-green-200 ${className}`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span>Saved {lastSaved.toLocaleTimeString()}</span>
      </div>
    );
  }

  return null;
}
