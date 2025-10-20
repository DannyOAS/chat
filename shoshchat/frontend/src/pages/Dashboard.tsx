import ChatWidget from "../components/ChatWidget";

const metrics = [
  { label: "Total Messages", value: "1,248" },
  { label: "Last Response Time", value: "320ms" },
  { label: "Active Plan", value: "Retail Pro" }
];

const Dashboard = () => {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-lg font-semibold">Usage Overview</h2>
        <p className="mt-1 text-sm text-slate-400">
          Monitor message volumes and response times for your tenants in real-time.
        </p>
        <dl className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <dt className="text-xs uppercase tracking-wide text-slate-400">{metric.label}</dt>
              <dd className="mt-2 text-2xl font-semibold text-white">{metric.value}</dd>
            </div>
          ))}
        </dl>
      </section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-lg font-semibold">Retail Persona Preview</h2>
        <p className="mt-1 text-sm text-slate-400">Interact with the tenant-specific widget.</p>
        <div className="mt-4 flex justify-center">
          <ChatWidget tenantId="retail-demo" accent="retail" />
        </div>
      </section>
      <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 md:col-span-2">
        <h2 className="text-lg font-semibold">Finance Persona Preview</h2>
        <p className="mt-1 text-sm text-slate-400">
          Preview compliance-aware responses for finance and insurance tenants.
        </p>
        <div className="mt-4 flex justify-center">
          <ChatWidget tenantId="finance-demo" accent="finance" />
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
