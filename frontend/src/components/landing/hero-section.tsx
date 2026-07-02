"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export default function HeroSection() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-primary/20 blur-[120px] rounded-full pointer-events-none opacity-50 dark:opacity-20" />
      
      <div className="max-w-7xl mx-auto px-6 relative z-10 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent text-accent-foreground text-xs font-medium mb-8 border border-border">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          ReputationOS AI 2.0 is now live
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl text-foreground mb-6 leading-tight">
          Automate your brand reputation with{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-foreground to-muted-foreground">
            Artificial Intelligence
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed">
          Monitor customer sentiments, automate review replies with custom brand voices, and analyze competitor intelligence metrics in real-time.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <Button asChild size="lg" className="rounded-full px-8 h-12 text-base w-full sm:w-auto">
            <Link href="/register">
              Start Free Trial <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="rounded-full px-8 h-12 text-base w-full sm:w-auto">
            <Link href="/login">View Live Demo</Link>
          </Button>
        </div>
        
        <div className="relative w-full max-w-5xl mx-auto rounded-2xl border border-border bg-card/50 backdrop-blur-xl p-2 md:p-4 shadow-2xl">
          <div className="relative w-full aspect-[16/9] rounded-lg overflow-hidden border border-border/50 bg-background">
            <Image 
              src="/hero.jpg" 
              alt="ReputationOS Dashboard"
              fill
              className="object-cover"
              priority
            />
          </div>
        </div>
      </div>
    </section>
  );
}
