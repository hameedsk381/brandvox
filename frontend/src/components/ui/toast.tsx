import { toast as hotToast } from "react-hot-toast";

export const toast = {
  success: (message: string) => hotToast.success(message, { style: { background: "#065f46", color: "#fff", borderRadius: "0.75rem" } }),
  error: (message: string) => hotToast.error(message, { style: { background: "#991b1b", color: "#fff", borderRadius: "0.75rem" } }),
  loading: (message: string) => hotToast.loading(message, { style: { background: "#1e3a5f", color: "#fff", borderRadius: "0.75rem" } }),
  dismiss: hotToast.dismiss,
};

export { Toaster } from "react-hot-toast";
