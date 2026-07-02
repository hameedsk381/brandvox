"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import PublicTopbar from "@/components/landing/public-topbar";
import HeroSection from "@/components/landing/hero-section";
import FeaturesSection from "@/components/landing/features-section";
import ShowcaseSection from "@/components/landing/showcase-section";
import Footer from "@/components/landing/footer";

export default function RootPage() {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Remove auto-redirect so the user can see the landing page!
  }, []);

  // Avoid hydration mismatch by waiting for mount
  if (!mounted) return null;

  return (
    <main className="min-h-screen bg-background flex flex-col">
      <PublicTopbar />
      <div className="flex-1">
        <HeroSection />
        <FeaturesSection />
        <ShowcaseSection />
        {/* Simple CTA before footer */}
        <section className="py-24 bg-card border-t border-border text-center">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground mb-6">
            Ready to supercharge your reputation?
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
            Join thousands of businesses using ReputationOS AI to automate their customer engagement.
          </p>
          <button
            onClick={() => router.push('/register')}
            className="inline-flex items-center justify-center rounded-full bg-foreground text-background px-8 h-12 text-base font-medium hover:bg-foreground/90 transition-colors"
          >
            Get Started for Free
          </button>
        </section>
      </div>
      <Footer />
    </main>
  );
}

