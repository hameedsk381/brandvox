"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import toast from "react-hot-toast";

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: { email: string; password: string }) => authAPI.login(data),
    onSuccess: (res) => {
      setAuth(res.access_token, res.user);
      toast.success("Welcome back!");
      router.push("/dashboard");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: { email: string; password: string; name: string }) => authAPI.register(data),
    onSuccess: (res) => {
      setAuth(res.access_token, res.user);
      toast.success("Account created!");
      router.push("/dashboard");
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();

  return () => {
    logout();
    router.push("/login");
  };
}

export function useCurrentUser() {
  return useAuthStore((state) => state.user);
}
