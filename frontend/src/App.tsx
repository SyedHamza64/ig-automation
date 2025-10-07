import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import ProfilesPage from "./pages/Profiles";
import AccountsPage from "./pages/Accounts";
import ActionsPage from "./pages/Actions";
import LimitsPage from "./pages/Limits";
import { ToastProvider } from "./components/ui/Toast";
import { DarkModeProvider } from "./contexts/DarkModeContext";
import { WarmupProgressProvider } from "./contexts/WarmupProgressContext";
import WarmupProgressIndicator from "./components/ui/WarmupProgressIndicator";

// (keep Placeholder for other routes if you want)
const Placeholder = ({ title }: { title: string }) => (
  <div className="text-lg font-semibold">{title}</div>
);

export default function App() {
  return (
    <DarkModeProvider>
      <ToastProvider>
        <WarmupProgressProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Overview />} />
              <Route path="/accounts" element={<AccountsPage />} />
              <Route path="/profiles" element={<ProfilesPage />} />
              <Route path="/actions" element={<ActionsPage />} />
              <Route path="/limits" element={<LimitsPage />} />
              <Route path="/logs" element={<Placeholder title="Logs" />} />
              <Route path="/templates" element={<Placeholder title="Templates" />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <WarmupProgressIndicator />
        </WarmupProgressProvider>
      </ToastProvider>
    </DarkModeProvider>
  );
}
