import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import api from "../lib/api";

const VerifyEmail = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = new URLSearchParams(location.search);
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"pending" | "success" | "error">("pending");

  useEffect(() => {
    const confirm = async () => {
      try {
        await api.post("/auth/email/verify/confirm/", { uid, token });
        setStatus("success");
        setTimeout(() => navigate("/login"), 2000);
      } catch (error) {
        console.error(error);
        setStatus("error");
      }
    };
    if (uid && token) {
      void confirm();
    } else {
      setStatus("error");
    }
  }, [uid, token, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 text-slate-100">
      <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center shadow-xl">
        {status === "pending" && <p className="text-sm text-slate-300">Verifying your email…</p>}
        {status === "success" && (
          <div className="space-y-3">
            <h1 className="text-2xl font-semibold text-emerald-300">Email verified!</h1>
            <p className="text-sm text-slate-400">Thanks for confirming. Redirecting you to sign in…</p>
          </div>
        )}
        {status === "error" && (
          <div className="space-y-3">
            <h1 className="text-2xl font-semibold text-red-300">Verification failed</h1>
            <p className="text-sm text-slate-400">The link may have expired. Request a new verification email from your profile.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
