"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authAPI, userAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import toast from "react-hot-toast";

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setMfaToken = useAuthStore((state) => state.setMfaToken);

  return useMutation({
    mutationFn: (data: { email: string; password: string }) => authAPI.login(data),
    onSuccess: (res) => {
      if (res.mfa_required) {
        setMfaToken(res.mfa_token);
        router.push("/login?mfa=1");
        return;
      }
      setAuth(res.access_token, res.user);
      toast.success("Welcome back!");
      router.push("/dashboard");
    },
  });
}

export function useVerifyMfaLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: (data: { mfa_token: string; code: string }) => authAPI.verifyMfaLogin(data),
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

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authAPI.changePassword(data),
    onSuccess: () => toast.success("Password changed successfully"),
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (data: { email: string }) => authAPI.forgotPassword(data),
    onSuccess: () => toast.success("If the email exists, a reset link has been sent"),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (data: { token: string; password: string }) => authAPI.resetPassword(data),
    onSuccess: () => {
      toast.success("Password has been reset. Please sign in.");
    },
  });
}

export function useExportMyData() {
  return useMutation({
    mutationFn: () => userAPI.exportMyData(),
  });
}

export function useDeleteMyAccount() {
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();

  return useMutation({
    mutationFn: () => userAPI.deleteMyAccount(),
    onSuccess: () => {
      logout();
      toast.success("Account deleted");
      router.push("/login");
    },
  });
}