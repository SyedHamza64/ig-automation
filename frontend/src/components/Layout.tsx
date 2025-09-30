import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { DarkModeToggle } from "./DarkModeToggle";

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <Sidebar />
      <div className="flex min-h-screen w-full flex-col">
        <Topbar />
        <main className="mx-auto w-full max-w-screen-2xl px-4 py-6">
          <Outlet />
        </main>
      </div>
      {/* Dark mode toggle - floating in bottom right */}
      <div className="fixed bottom-4 right-4 z-50">
        <DarkModeToggle />
      </div>
    </div>
  );
}