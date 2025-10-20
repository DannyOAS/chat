import { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { hasSession } from "../lib/auth";

interface RequireAuthProps {
  children: ReactElement;
}

const RequireAuth = ({ children }: RequireAuthProps) => {
  const location = useLocation();

  if (!hasSession()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
};

export default RequireAuth;
