export default function Topbar() {
    return (
      <header className="sticky top-0 z-10 border-b bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-12 max-w-screen-2xl items-center justify-between px-4">
          <div className="text-sm text-gray-600">Dashboard</div>
          <div className="text-xs text-gray-500">Dev mode • No login</div>
        </div>
      </header>
    );
  }