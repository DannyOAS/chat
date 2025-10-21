import { createContext, ReactNode, useContext, useEffect, useState } from "react";

import api from "../lib/api";
import { hasSession } from "../lib/auth";

interface TenantPlan {
  name: string;
  slug: string;
  monthly_price: string;
  message_quota: number;
  current_period_start?: string;
  current_period_end?: string;
}

interface TenantDomain {
  domain: string;
  is_primary: boolean;
}

interface TenantDetails {
  id: number | string;
  name: string;
  schema_name: string;
  industry: string;
  widget_accent: string;
  widget_welcome_message: string;
  widget_primary_color: string;
  paid_until?: string | null;
  on_trial: boolean;
  plan: TenantPlan | null;
  domains: TenantDomain[];
}

interface TenantContextValue {
  tenant: TenantDetails | null;
  refresh: () => Promise<void>;
  loading: boolean;
}

const TenantContext = createContext<TenantContextValue | undefined>(undefined);

export const TenantProvider = ({ children }: { children: ReactNode }) => {
  const [tenant, setTenant] = useState<TenantDetails | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchTenant = async () => {
    if (!hasSession()) {
      setLoading(false);
      setTenant(null);
      return;
    }
    try {
      setLoading(true);
      const response = await api.get<TenantDetails>("/tenants/me/");
      setTenant(response.data);
    } catch (error) {
      console.error("Failed to load tenant", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchTenant();
  }, []);

  return (
    <TenantContext.Provider value={{ tenant, refresh: fetchTenant, loading }}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error("useTenant must be used within TenantProvider");
  }
  return context;
};
