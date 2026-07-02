"use client";

import { useQuery } from "@tanstack/react-query";
import { settingsAPI } from "@/lib/api";
import { useBrandingStore } from "@/stores/branding-store";
import { useAuthStore } from "@/stores/auth-store";
import { useEffect } from "react";

export function useBranding() {
  const user = useAuthStore((state) => state.user);
  const setBranding = useBrandingStore((state) => state.setBranding);

  const query = useQuery({
    queryKey: ["branding", user?.agency_id],
    queryFn: () => settingsAPI.getBranding(user!.agency_id!),
    enabled: !!user?.agency_id,
  });

  useEffect(() => {
    if (query.data) {
      setBranding(query.data);
    }
  }, [query.data, setBranding]);

  return query;
}
