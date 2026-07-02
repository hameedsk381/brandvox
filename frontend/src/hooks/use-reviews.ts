"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewsAPI, ReviewsListParams, CreateReviewData, SubmitReplyData } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import toast from "react-hot-toast";

export function useReviews(params?: ReviewsListParams) {
  const currentLocation = useTenantStore((state) => state.currentLocation);

  return useQuery({
    queryKey: ["reviews", currentLocation?.id, params],
    queryFn: () => reviewsAPI.list({ location_id: currentLocation?.id, ...params }),
    enabled: !!currentLocation?.id,
  });
}

export function useReview(id: string) {
  return useQuery({
    queryKey: ["review", id],
    queryFn: () => reviewsAPI.get(id),
    enabled: !!id,
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReviewData) => reviewsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      toast.success("Review added");
    },
    onError: () => toast.error("Failed to add review"),
  });
}

export function useGenerateAIReply() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reviewId: string) => reviewsAPI.generateAIReply(reviewId),
    onSuccess: (_, reviewId) => {
      queryClient.invalidateQueries({ queryKey: ["review", reviewId] });
      toast.success("AI reply generated");
    },
    onError: () => toast.error("Failed to generate AI reply"),
  });
}

export function useSubmitReply() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reviewId, data }: { reviewId: string; data: SubmitReplyData }) =>
      reviewsAPI.submitReply(reviewId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      toast.success("Reply submitted");
    },
    onError: () => toast.error("Failed to submit reply"),
  });
}

export function useApproveReply() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (replyId: string) => reviewsAPI.approveReply(replyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      toast.success("Reply approved");
    },
    onError: () => toast.error("Failed to approve reply"),
  });
}

export function useRejectReply() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (replyId: string) => reviewsAPI.rejectReply(replyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
      toast.success("Reply rejected");
    },
    onError: () => toast.error("Failed to reject reply"),
  });
}
