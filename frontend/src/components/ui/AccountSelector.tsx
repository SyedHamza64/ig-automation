// frontend/src/components/ui/AccountSelector.tsx


interface Account {
  id: number;
  handle: string;
  instagram_username?: string | null;
  status?: string;
}

interface AccountSelectorProps {
  accounts: Account[];
  selectedAccountId: number | null;
  onAccountChange: (accountId: number) => void;
  className?: string;
  placeholder?: string;
  showStatus?: boolean;
}

export function AccountSelector({ 
  accounts, 
  selectedAccountId, 
  onAccountChange, 
  className = "", 
  placeholder = "Select an account...",
  showStatus = false
}: AccountSelectorProps) {
  const getStatusColor = (status?: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-50 border-green-200";
      case "warn":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "blocked":
        return "text-red-600 bg-red-50 border-red-200";
      case "new":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className={`relative ${className}`}>
      <select
        value={selectedAccountId ?? ""}
        onChange={(e) => onAccountChange(Number(e.target.value))}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
      >
        <option value="">{placeholder}</option>
        {accounts.map((account) => (
          <option key={account.id} value={account.id}>
            {account.handle} {account.instagram_username && `(@${account.instagram_username})`}
          </option>
        ))}
      </select>
      
      {/* Custom dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Selected account info */}
      {selectedAccountId && showStatus && (
        <div className="mt-2">
          {(() => {
            const selectedAccount = accounts.find(acc => acc.id === selectedAccountId);
            if (!selectedAccount) return null;
            
            return (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Status:
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(selectedAccount.status)}`}>
                  {selectedAccount.status}
                </span>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}

interface AccountInfoProps {
  account: Account | null;
  className?: string;
}

export function AccountInfo({ account, className = "" }: AccountInfoProps) {
  if (!account) return null;

  const getStatusColor = (status?: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-50 border-green-200";
      case "warn":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "blocked":
        return "text-red-600 bg-red-50 border-red-200";
      case "new":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {account.handle}
        </h3>
        {account.instagram_username && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            @{account.instagram_username}
          </p>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(account.status)}`}>
          {account.status}
        </span>
      </div>
    </div>
  );
}
