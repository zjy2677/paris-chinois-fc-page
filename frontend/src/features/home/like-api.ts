import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export type HomepageLikeState = {
  count: number;
  liked: boolean;
};

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
const queryKey = ["homepage", "likes"] as const;

async function request(method: "GET" | "POST" | "DELETE", signal?: AbortSignal) {
  const response = await fetch(`${base}/api/likes`, {
    method,
    credentials: "include",
    ...(signal ? { signal } : {}),
  });
  if (!response.ok) throw new Error(`Likes request failed: ${response.status}`);
  return response.json() as Promise<HomepageLikeState>;
}

export function useHomepageLikes() {
  return useQuery({
    queryKey,
    enabled: typeof window !== "undefined",
    queryFn: ({ signal }) => request("GET", signal),
  });
}

export function useToggleHomepageLike() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (liked: boolean) => request(liked ? "DELETE" : "POST"),
    onSuccess: (state) => queryClient.setQueryData(queryKey, state),
  });
}
