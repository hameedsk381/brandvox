"use client";

import React from "react";
import { useReviews } from "@/hooks/use-reviews";
import { useTenantStore } from "@/stores/tenant-store";
import { useFilterStore } from "@/stores/filter-store";
import ReviewCard from "@/components/reviews/review-card";
import ReviewFilters from "@/components/reviews/review-filters";
import { Review } from "@/types";
import { ReviewsListSkeleton } from "@/components/ui/page-skeleton";

export default function ReviewsPage() {
  const currentFilters = useFilterStore((state) => state.currentFilters);
  const setCurrentFilters = useFilterStore((state) => state.setCurrentFilters);
  const currentLocation = useTenantStore((state) => state.currentLocation);
  const { data, isLoading } = useReviews(currentFilters);

  return (
    <div className="max-w-7xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Reviews</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {currentLocation?.name || "All locations"} &mdash; {data?.total || data?.items?.length || 0} reviews
        </p>
      </div>

      <ReviewFilters onFilter={setCurrentFilters} />

      {isLoading ? (
        <ReviewsListSkeleton />
      ) : !data?.items || data.items.length === 0 ? (
        <div className="glass-panel rounded-xl p-12 text-center">
          <p className="text-muted-foreground">No reviews found</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {(data.items as Review[]).map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </div>
      )}
    </div>
  );
}
