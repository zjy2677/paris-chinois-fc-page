import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export type BlogStatus = "draft" | "pending" | "published" | "rejected";
export type BlogPost = {
  id: string;
  title: string;
  body: string;
  status: BlogStatus;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};
export type BlogInput = Pick<BlogPost, "title" | "body">;

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}/api/blog${path}`, {
    credentials: "include",
    ...init,
    ...(init?.body ? { headers: { "Content-Type": "application/json" } } : {}),
  });
  if (!response.ok) throw new Error(`Blog request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function usePublishedPosts() {
  return useQuery({
    queryKey: ["blog", "published"],
    queryFn: () => request<{ items: BlogPost[]; total: number }>("/posts"),
  });
}

export function usePublishedPost(id: string) {
  return useQuery({
    queryKey: ["blog", "post", id],
    queryFn: () => request<BlogPost>(`/posts/${id}`),
  });
}

export function useMyPosts(enabled: boolean) {
  return useQuery({
    queryKey: ["blog", "mine"],
    enabled,
    queryFn: () => request<BlogPost[]>("/mine"),
  });
}

export function useModerationQueue(enabled: boolean) {
  return useQuery({
    queryKey: ["blog", "moderation"],
    enabled,
    queryFn: () => request<BlogPost[]>("/moderation"),
  });
}

export function useBlogMutation() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: ({ path, method, body }: { path: string; method?: string; body?: object }) =>
      request<BlogPost>(path, {
        method: method ?? "POST",
        ...(body ? { body: JSON.stringify(body) } : {}),
      }),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ["blog"] });
    },
  });
}
