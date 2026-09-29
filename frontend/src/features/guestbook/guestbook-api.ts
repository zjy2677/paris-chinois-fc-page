import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export type GuestbookMessage = {
  id: string;
  nickname: string;
  body: string;
  status: "visible" | "hidden";
  created_at: string;
};

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}/api/guestbook${path}`, {
    credentials: "include",
    ...init,
    ...(init?.body ? { headers: { "Content-Type": "application/json" } } : {}),
  });
  if (!response.ok) throw new Error(`Guestbook request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export function useGuestbookMessages() {
  return useQuery({
    queryKey: ["guestbook", "messages"],
    queryFn: () => request<GuestbookMessage[]>("/messages"),
  });
}

export function useGuestbookModeration(enabled: boolean) {
  return useQuery({
    queryKey: ["guestbook", "moderation"],
    enabled,
    queryFn: () => request<GuestbookMessage[]>("/moderation"),
  });
}

export function useGuestbookMutation() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: ({ path, body }: { path: string; body?: object }) =>
      request<GuestbookMessage>(path, {
        method: "POST",
        ...(body ? { body: JSON.stringify(body) } : {}),
      }),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ["guestbook"] });
    },
  });
}
