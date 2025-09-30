import { NavLink } from "react-router-dom";
import { Home, Users, MonitorCog, PlayCircle, ListChecks, Gauge, FileText } from "lucide-react";

const nav = [
  { to: "/", label: "Overview", icon: Home },
  { to: "/accounts", label: "Accounts", icon: Users },
  { to: "/profiles", label: "Profiles", icon: MonitorCog },
  { to: "/actions", label: "Actions", icon: PlayCircle },
  { to: "/logs", label: "Logs", icon: ListChecks },
  { to: "/limits", label: "Limits", icon: Gauge },
  { to: "/templates", label: "Templates", icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="px-4 py-4 text-lg font-semibold text-gray-900 dark:text-white">IG Automation</div>
      <nav className="space-y-1 px-2">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 ${
                isActive 
                  ? "bg-gray-100 font-medium text-gray-900 dark:bg-gray-700 dark:text-white" 
                  : "text-gray-700 dark:text-gray-300"
              }`
            }
          >
            <Icon size={16} /> {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}