import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      <Sidebar />
      <div className="flex min-h-screen w-full flex-col">
        <Topbar />
        <main className="mx-auto w-full max-w-screen-2xl px-4 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}