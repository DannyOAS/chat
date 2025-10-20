import { ReactNode } from "react";

interface DashboardLayoutProps {
  children: ReactNode;
}

const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold">ShoshChat AI</h1>
            <p className="text-sm text-slate-400">Multi-tenant AI chat orchestration</p>
          </div>
          <nav className="flex items-center gap-4 text-sm text-slate-400">
            <a href="#" className="hover:text-white">
              Dashboard
            </a>
            <a href="#" className="hover:text-white">
              Billing
            </a>
            <a href="#" className="hover:text-white">
              Settings
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-8">{children}</main>
    </div>
  );
};

export default DashboardLayout;
