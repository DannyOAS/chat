import { ReactNode, useMemo } from "react";
import { useNavigate } from "react-router-dom";

import { clearSession, getStoredUser } from "../lib/auth";

interface DashboardLayoutProps {
  children: ReactNode;
}

const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  const navigate = useNavigate();
  const user = useMemo(() => getStoredUser(), []);

  const handleSignOut = () => {
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold">ShoshChat AI</h1>
            <p className="text-sm text-slate-400">Multi-tenant AI chat orchestration</p>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            {user ? (
              <span className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs uppercase tracking-wide text-slate-300">
                {user.username}
              </span>
            ) : null}
            <button
              type="button"
              onClick={handleSignOut}
              className="rounded-lg border border-slate-700 px-3 py-1 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-8">{children}</main>
    </div>
  );
};

export default DashboardLayout;
