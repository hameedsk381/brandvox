"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
 LayoutDashboard,
 MessageSquare,
 BarChart3,
 FileText,
 Link2,
 Volume2,
 Cpu,
 Palette,
 Users,
 X,
 LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useBrandingStore } from "@/stores/branding-store";
import { useLogout } from "@/hooks/use-auth";
import { ROUTES } from "@/lib/constants";

interface MobileNavProps {
 isOpen: boolean;
 onClose: () => void;
}

export default function MobileNav({ isOpen, onClose }: MobileNavProps) {
 const pathname = usePathname();
 const user = useAuthStore((state) => state.user);
 const config = useBrandingStore((state) => state.brandingConfig);
 const logout = useLogout();
 const brandName = config?.company_name || "ReputationOS AI";

 const mainNav = [
 { label: "Dashboard", href: ROUTES.DASHBOARD, icon: LayoutDashboard },
 { label: "Reviews", href: ROUTES.REVIEWS, icon: MessageSquare },
 { label: "Analytics", href: ROUTES.ANALYTICS, icon: BarChart3 },
 { label: "Reports", href: ROUTES.REPORTS, icon: FileText },
 { label: "Integrations", href: ROUTES.INTEGRATIONS, icon: Link2 },
 ];

 const settingsNav = [
 { label: "Brand Voice", href: ROUTES.BRAND_VOICE, icon: Volume2 },
 { label: "Smart Rules", href: ROUTES.SMART_RULES, icon: Cpu },
 { label: "Branding", href: ROUTES.BRANDING, icon: Palette },
 { label: "Team", href: ROUTES.TEAM, icon: Users },
 ];

 if (!isOpen) return null;

 return (
 <div className="fixed inset-0 z-50 lg:hidden">
 <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
 <div className="fixed left-0 top-0 bottom-0 w-72 glass-panel border-r border-border/60 flex flex-col z-10 animate-in slide-in-from-left duration-200">
 <div className="h-16 flex items-center justify-between px-4 border-b border-border/60">
 <div className="flex items-center gap-2 font-bold text-lg bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
 <span className="w-6 h-6 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-xs">R</span>
 {brandName}
 </div>
 <button onClick={onClose} className="p-2 rounded-lg hover:bg-muted text-muted-foreground cursor-pointer">
 <X className="w-5 h-5" />
 </button>
 </div>

 <div className="flex-1 py-4 flex flex-col gap-1.5 overflow-y-auto px-3">
 {mainNav.map((item) => {
 const isActive = pathname === item.href;
 const Icon = item.icon;
 return (
 <Link
 key={item.href}
 href={item.href}
 onClick={onClose}
 className={cn(
 "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all",
 isActive ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
 )}
 >
 <Icon className="w-5 h-5 shrink-0" />
 <span>{item.label}</span>
 </Link>
 );
 })}

 <div className="mt-4 text-muted-foreground font-bold uppercase tracking-wider text-[10px] px-3 mb-1">
 Settings
 </div>
 {settingsNav.map((sub) => {
 const isSubActive = pathname === sub.href;
 const SubIcon = sub.icon;
 return (
 <Link
 key={sub.href}
 href={sub.href}
 onClick={onClose}
 className={cn(
 "flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-all pl-5",
 isSubActive ? "bg-accent text-accent-foreground font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
 )}
 >
 <SubIcon className="w-4 h-4 shrink-0" />
 <span>{sub.label}</span>
 </Link>
 );
 })}
 </div>

 <div className="p-3 border-t border-border/60">
 <div className="flex items-center gap-3 px-2 py-1.5 rounded-lg bg-muted/50 mb-2">
 <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-secondary-foreground font-bold text-xs">
 {user?.name?.slice(0, 2).toUpperCase() || "US"}
 </div>
 <div className="flex-1 overflow-hidden">
 <div className="text-xs font-semibold text-foreground truncate">{user?.name}</div>
 <div className="text-[10px] text-muted-foreground truncate uppercase tracking-wider">{user?.role?.replace("_", " ")}</div>
 </div>
 </div>
 <button
 onClick={() => { logout(); onClose(); }}
 className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium text-rose-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all cursor-pointer"
 >
 <LogOut className="w-4 h-4" /> Logout
 </button>
 </div>
 </div>
 </div>
 );
}


