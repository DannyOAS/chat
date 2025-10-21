import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import api from "../lib/api";
import { login, register as registerUser } from "../lib/auth";

interface Plan {
  slug: string;
  name: string;
  monthly_price: string;
  message_quota: number;
  features: string[];
}

const defaultWelcome = "Hi there! I'm excited to help you today.";

const Register = () => {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string>("");
  const [form, setForm] = useState({
    company_name: "",
    industry: "retail",
    domain: "",
    accent: "retail",
    welcome_message: defaultWelcome,
    primary_color: "#14b8a6",
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await api.get<Plan[]>("/billing/plans/");
        setPlans(response.data);
        if (response.data.length > 0) {
          setSelectedPlan(response.data[0].slug);
        }
      } catch (err) {
        console.error("Failed to load plans", err);
      }
    };
    void fetchPlans();
  }, []);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const selectedPlanDetails = useMemo(() => plans.find((plan) => plan.slug === selectedPlan), [plans, selectedPlan]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await registerUser({
        username: form.username,
        email: form.email,
        password: form.password,
        password_confirm: form.password_confirm,
        first_name: form.first_name,
        last_name: form.last_name,
        company_name: form.company_name,
        industry: form.industry,
        plan: selectedPlan,
        domain: form.domain,
        accent: form.accent,
        welcome_message: form.welcome_message,
        primary_color: form.primary_color,
      });
      await login(form.username, form.password);
      navigate("/onboarding", { replace: true });
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail ?? "Unable to complete registration");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-10 lg:flex-row">
        <div className="w-full max-w-md space-y-6 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl">
          <div>
            <h1 className="text-3xl font-semibold">Create your ShoshChat account</h1>
            <p className="mt-2 text-sm text-slate-400">Start chatting with your customers in minutes.</p>
          </div>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Company Name</label>
              <input
                name="company_name"
                value={form.company_name}
                onChange={handleChange}
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Industry</label>
                <select
                  name="industry"
                  value={form.industry}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                >
                  <option value="retail">Retail / E-commerce</option>
                  <option value="finance">Finance / Insurance</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Domain (optional)</label>
                <input
                  name="domain"
                  value={form.domain}
                  onChange={handleChange}
                  placeholder="chat.yourdomain.com"
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">First Name</label>
                <input
                  name="first_name"
                  value={form.first_name}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Last Name</label>
                <input
                  name="last_name"
                  value={form.last_name}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Business Email</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Username</label>
              <input
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Password</label>
                <input
                  name="password"
                  type="password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Confirm Password</label>
                <input
                  name="password_confirm"
                  type="password"
                  value={form.password_confirm}
                  onChange={handleChange}
                  required
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs uppercase tracking-wide text-slate-400">Welcome Message</label>
              <textarea
                name="welcome_message"
                value={form.welcome_message}
                onChange={handleChange}
                rows={3}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Widget Accent</label>
                <select
                  name="accent"
                  value={form.accent}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500"
                >
                  <option value="retail">Retail</option>
                  <option value="finance">Finance</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wide text-slate-400">Primary Color</label>
                <input
                  name="primary_color"
                  type="color"
                  value={form.primary_color}
                  onChange={handleChange}
                  className="h-12 w-full cursor-pointer rounded-lg border border-slate-800 bg-slate-950"
                />
              </div>
            </div>

            {error ? (
              <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              className="w-full rounded-xl bg-blue-500 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Creating account…" : "Create account"}
            </button>
            <p className="text-xs text-slate-500">
              Already have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
            </p>
          </form>
        </div>
        <div className="flex-1 space-y-6">
          <section className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
            <h2 className="text-lg font-semibold">Select a plan</h2>
            <p className="mt-1 text-sm text-slate-400">Scale your AI assistant with usage-based tiers.</p>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {plans.map((plan) => (
                <button
                  key={plan.slug}
                  type="button"
                  onClick={() => setSelectedPlan(plan.slug)}
                  className={`rounded-2xl border p-4 text-left transition ${
                    selectedPlan === plan.slug
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-100">{plan.name}</h3>
                    <span className="text-sm text-slate-400">${plan.monthly_price}/mo</span>
                  </div>
                  <p className="mt-2 text-xs text-slate-400">{plan.message_quota} messages / month</p>
                  <ul className="mt-3 space-y-1 text-xs text-slate-400">
                    {plan.features.map((feature) => (
                      <li key={feature}>• {feature}</li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
            {selectedPlanDetails ? (
              <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm text-slate-300">
                <h3 className="font-semibold text-slate-100">{selectedPlanDetails.name} includes:</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-400">
                  {selectedPlanDetails.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
          <section className="rounded-3xl border border-slate-800 bg-slate-900/40 p-6">
            <h2 className="text-lg font-semibold">Preview your widget</h2>
            <p className="mt-1 text-sm text-slate-400">Customize the look before embedding.</p>
            <div className="mt-4 flex justify-center">
              <div className="w-80 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="space-y-2 text-sm">
                  <p className="text-slate-300">{form.welcome_message}</p>
                  <div className="rounded-xl bg-slate-800/60 p-3">
                    <span className="text-xs uppercase tracking-wide text-slate-400">Accent</span>
                    <p className="text-sm text-slate-100">{form.accent}</p>
                  </div>
                  <div className="rounded-xl bg-slate-800/60 p-3">
                    <span className="text-xs uppercase tracking-wide text-slate-400">Primary Color</span>
                    <div className="mt-2 h-8 w-full rounded-lg" style={{ backgroundColor: form.primary_color }} />
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default Register;
