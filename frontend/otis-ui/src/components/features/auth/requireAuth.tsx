// RequireAuth.tsx
import { useAuth } from "@/authContext";
import type { JSX } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Spinner } from "@/components/ui/spinner";

export function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  const token = localStorage.getItem("access_token");

  if (loading) {
    return (
      <div className="flex items-center gap-4 justify-center min-h-screen w-full">
        <Spinner />
      </div>
    );
  }

  if (!token || !user) {
    return (
      <Navigate
        to="/Login"
        replace
        state={{ from: location.pathname || "/" }}
      />
    );
  }

  return children;
}
