"use client";

import React from "react";
import Image from "next/image";
import { CheckCircle2 } from "lucide-react";

export default function ShowcaseSection() {
  return (
    <section id="showcase" className="py-24 bg-background border-t border-border/50">
      <div className="max-w-7xl mx-auto px-6 flex flex-col gap-32">
        
        {/* Feature 1 */}
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="order-2 md:order-1 relative aspect-[4/3] rounded-2xl overflow-hidden border border-border shadow-xl">
            <Image 
              src="/ai_reply.jpg" 
              alt="AI Reply Generation" 
              fill
              className="object-cover"
            />
          </div>
          <div className="order-1 md:order-2">
            <h2 className="text-3xl font-bold tracking-tight text-foreground mb-6">
              Never write a manual review reply again.
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Our advanced language models analyze the customer's sentiment, identify key topics, and draft the perfect response tailored to your specific brand voice and industry guidelines.
            </p>
            <ul className="flex flex-col gap-4">
              {["Custom brand voice profiles (Tone, Vocab, Emojis)", "Human-in-the-loop approval workflows", "Multi-lingual reply generation"].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-foreground shrink-0" />
                  <span className="text-foreground">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Feature 2 */}
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-foreground mb-6">
              Turn qualitative feedback into quantitative metrics.
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Stop guessing how your customers feel. We automatically categorize reviews by topic (e.g., Food Quality, Wait Time, Hygiene) and track sentiment trends over time.
            </p>
            <ul className="flex flex-col gap-4">
              {["Proprietary Reputation Score™ algorithm", "Automated topic extraction and tagging", "Custom PDF & CSV reporting exports"].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-foreground shrink-0" />
                  <span className="text-foreground">{item}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="relative aspect-[4/3] rounded-2xl overflow-hidden border border-border shadow-xl">
            <Image 
              src="/analytics.jpg" 
              alt="Reputation Analytics" 
              fill
              className="object-cover"
            />
          </div>
        </div>

      </div>
    </section>
  );
}
