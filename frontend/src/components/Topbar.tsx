export default function Topbar() {
    return (
      <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur dark:border-gray-700 dark:bg-gray-800/80">
        <div className="mx-auto flex h-12 max-w-screen-2xl items-center justify-between px-4">
          <div className="text-sm text-gray-600 dark:text-gray-300">Dashboard</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">Dev mode • No login</div>
        </div>
      </header>
    );
  }