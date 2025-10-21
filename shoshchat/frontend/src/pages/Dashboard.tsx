import { FormEvent, useEffect, useMemo, useState } from "react";

import api from "../lib/api";
import ChatWidget from "../components/ChatWidget";
import { useTenant } from "../context/TenantContext";

interface UsageSummary {
  message_count: number;
  period_start: string;
  period_end: string;
  last_message_at: string | null;
}

interface PlanOption {
  slug: string;
  name: string;
  monthly_price: string;
  message_quota: number;
  features: string[];
}

interface AnalyticsResponse {
  total_sessions: number;
  total_messages: number;
  role_breakdown: Record<string, number>;
  recent_sessions: { user_id: string; last_interaction_at: string }[];
}

const Dashboard = () => {
  const { tenant, refresh: refreshTenant, loading } = useTenant();
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [embedCode, setEmbedCode] = useState<string>("");
  const [switchingPlan, setSwitchingPlan] = useState(false);
  const [updatingWidget, setUpdatingWidget] = useState(false);
  const [domainValue, setDomainValue] = useState("");
  const [savingDomain, setSavingDomain] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usageResponse, planResponse, analyticsResponse, embedResponse] = await Promise.all([
          api.get<UsageSummary>("/billing/usage/"),
          api.get<PlanOption[]>("/billing/plans/"),
          api.get<AnalyticsResponse>("/chat/analytics/"),
          api.get<{ embed_code: string }>("/tenants/me/embed/"),
        ]);
        setUsage(usageResponse.data);
        setPlans(planResponse.data);
        setAnalytics(analyticsResponse.data);
        setEmbedCode(embedResponse.data.embed_code);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      }
    };
    if (!loading) {
      void loadData();
    }
  }, [loading]);

  const currentPlan = useMemo(() => tenant?.plan, [tenant]);

  const handlePlanSwitch = async (plan: string) => {
    setSwitchingPlan(true);
    try {
      await api.post("/billing/subscription/switch/", { plan });
      await refreshTenant();
    } catch (error) {
      console.error("Failed to switch plan", error);
    } finally {
      setSwitchingPlan(false);
    }
  };

  const handleWidgetUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!tenant) return;
    setUpdatingWidget(true);
    const formData = new FormData(event.currentTarget);
    const payload = {
      widget_accent: formData.get("widget_accent"),
      widget_welcome_message: formData.get("widget_welcome_message"),
      widget_primary_color: formData.get("widget_primary_color"),
    };
    try {
      await api.patch("/tenants/me/settings/", payload);
      await refreshTenant();
    } catch (error) {
      console.error("Failed to update widget", error);
    } finally {
      setUpdatingWidget(false);
    }
  };

  const handleDomainAdd = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!domainValue) return;
    setSavingDomain(true);
    try {
      await api.post("/tenants/me/domains/", { domain: domainValue, is_primary: true });
      setDomainValue("");
      await refreshTenant();
    } catch (error) {
      console.error("Unable to save domain", error);
    } finally {
      setSavingDomain(false);
    }
  };

  return (
    <div className="space-y-8">
      <section className="grid gap-6 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-xs uppercase tracking-wide text-slate-400">Total Sessions</p>
          <p className="mt-3 text-3xl font-semibold text-white">{analytics?.total_sessions ?? "—"}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-xs uppercase tracking-wide text-slate-400">Messages</p>
          <p className="mt-3 text-3xl font-semibold text-white">{analytics?.total_messages ?? "—"}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <p className="text-xs uppercase tracking-wide text-slate-400">Plan</p>
          <p className="mt-3 text-xl font-semibold text-white">
            {currentPlan ? `${currentPlan.name} • ${currentPlan.message_quota} msgs` : "Trial"}
          </p>
          {tenant?.paid_until ? (
            <p className="mt-1 text-xs text-slate-400">Paid through {new Date(tenant.paid_until).toLocaleDateString()}</p>
          ) : (
            <p className="mt-1 text-xs text-amber-400">Currently on trial</p>
          )}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-lg font-semibold">Widget customization</h2>
          <p className="mt-1 text-sm text-slate-400">Instantly reflected in your embedded widget.</p>
          <form className="mt-6 space-y-4" onSubmit={handleWidgetUpdate}>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Accent</label>
              <select
                name="widget_accent"
                defaultValue={tenant?.widget_accent ?? "retail"}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              >
                <option value="retail">Retail</option>
                <option value="finance">Finance</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Welcome message</label>
              <textarea
                name="widget_welcome_message"
                defaultValue={tenant?.widget_welcome_message ?? ""}
                rows={3}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Primary color</label>
              <input
                name="widget_primary_color"
                type="color"
                defaultValue={tenant?.widget_primary_color ?? "#14b8a6"}
                className="h-12 w-full cursor-pointer rounded-xl border border-slate-800 bg-slate-950"
              />
            </div>
            <button
              type="submit"
              className="rounded-xl bg-blue-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-400 disabled:opacity-60"
              disabled={updatingWidget}
            >
              {updatingWidget ? "Saving…" : "Save changes"}
            </button>
          </form>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-lg font-semibold">Widget preview</h2>
          <p className="mt-1 text-sm text-slate-400">Real-time preview reflecting your settings.</p>
          <div className="mt-4 flex justify-center">
            <ChatWidget
              tenantId={tenant?.schema_name ?? "preview"}
              accent={(tenant?.widget_accent as "retail" | "finance") ?? "retail"}
            />
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-lg font-semibold">Manage subscription</h2>
          <p className="mt-1 text-sm text-slate-400">Upgrade or downgrade anytime.</p>
          <div className="mt-4 grid gap-4">
            {plans.map((plan) => {
              const isCurrent = plan.slug === currentPlan?.slug;
              return (
                <div
                  key={plan.slug}
                  className={`rounded-2xl border p-4 ${
                    isCurrent ? "border-emerald-500 bg-emerald-500/10" : "border-slate-800 bg-slate-900/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                    <span className="text-sm text-slate-400">${plan.monthly_price}/month</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{plan.message_quota} messages / month</p>
                  <ul className="mt-3 space-y-1 text-xs text-slate-400">
                    {plan.features.map((feature) => (
                      <li key={feature}>• {feature}</li>
                    ))}
                  </ul>
                  {!isCurrent ? (
                    <button
                      type="button"
                      onClick={() => handlePlanSwitch(plan.slug)}
                      className="mt-3 rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-slate-500"
                      disabled={switchingPlan}
                    >
                      {switchingPlan ? "Switching…" : "Switch to this plan"}
                    </button>
                  ) : (
                    <span className="mt-3 inline-flex items-center rounded-full border border-emerald-600 px-3 py-1 text-xs font-medium text-emerald-300">
                      Current plan
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-lg font-semibold">Team & Domains</h2>
          <p className="mt-1 text-sm text-slate-400">Configure where the widget appears.</p>
          <form className="mt-4 space-y-3" onSubmit={handleDomainAdd}>
            <label className="text-xs uppercase tracking-wide text-slate-400">Primary domain</label>
            <div className="flex gap-3">
              <input
                value={domainValue}
                onChange={(event) => setDomainValue(event.target.value)}
                placeholder="support.yourdomain.com"
                className="flex-1 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
              <button
                type="submit"
                className="rounded-xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 transition hover:bg-white disabled:opacity-60"
                disabled={savingDomain}
              >
                {savingDomain ? "Saving…" : "Save"}
              </button>
            </div>
          </form>
          <div className="mt-6 space-y-3">
            <h3 className="text-xs uppercase tracking-wide text-slate-400">Current domains</h3>
            {tenant?.domains?.length ? (
              <ul className="space-y-2 text-sm text-slate-300">
                {tenant.domains.map((domain) => (
                  <li key={domain.domain} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-2">
                    <span>{domain.domain}</span>
                    {domain.is_primary ? (
                      <span className="text-xs text-emerald-400">Primary</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No domains configured yet.</p>
            )}
          </div>
          <div className="mt-6">
            <h3 className="text-xs uppercase tracking-wide text-slate-400">Embed snippet</h3>
            <pre className="mt-2 max-h-40 overflow-x-auto whitespace-pre-wrap rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-[11px] text-slate-300">
              <code>{embedCode}</code>
            </pre>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold">Recent conversations</h2>
        <p className="mt-1 text-sm text-slate-400">Monitor activity from the last few visitors.</p>
        <div className="mt-4 space-y-3">
          {analytics?.recent_sessions.length ? (
            analytics.recent_sessions.map((session) => (
              <div key={session.user_id} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-sm text-slate-300">
                <span>{session.user_id}</span>
                <span className="text-xs text-slate-500">
                  {new Date(session.last_interaction_at).toLocaleString()}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-500">No sessions yet.</p>
          )}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-lg font-semibold">Usage summary</h2>
        {usage ? (
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
              <p className="text-xs uppercase tracking-wide text-slate-400">Messages</p>
              <p className="mt-2 text-2xl font-semibold text-white">{usage.message_count}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
              <p className="text-xs uppercase tracking-wide text-slate-400">Period start</p>
              <p className="mt-2 text-sm">{new Date(usage.period_start).toLocaleDateString()}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
              <p className="text-xs uppercase tracking-wide text-slate-400">Period end</p>
              <p className="mt-2 text-sm">{new Date(usage.period_end).toLocaleDateString()}</p>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-xs text-slate-500">Usage data will appear after your first conversations.</p>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
