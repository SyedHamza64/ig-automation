import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import AccountsPage from "./pages/Accounts"; // ⬅️ add this import

// (keep Placeholder for other routes if you want)
const Placeholder = ({ title }: { title: string }) => (
  <div className="text-lg font-semibold">{title}</div>
);

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="/accounts" element={<AccountsPage />} /> {/* ⬅️ use real page */}
        <Route path="/profiles" element={<Placeholder title="Profiles" />} />
        <Route path="/actions" element={<Placeholder title="Actions" />} />
        <Route path="/logs" element={<Placeholder title="Logs" />} />
        <Route path="/limits" element={<Placeholder title="Limits" />} />
        <Route path="/templates" element={<Placeholder title="Templates" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
