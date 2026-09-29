import { useQuery } from "@tanstack/react-query";
export type Account = {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  age_at_registration: number | null;
  role: "user" | "player" | "admin";
  avatar_updated_at: string | null;
};
const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");
export class AuthError extends Error {
  constructor(public status: number) {
    super("Authentication request failed");
  }
}
export async function authRequest<T>(
  path: string,
  body?: Record<string, string | number>,
): Promise<T> {
  const response = await fetch(`${base}/api/auth/${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) throw new AuthError(response.status);
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}

export async function uploadAvatar(file: File): Promise<void> {
  const response = await fetch(`${base}/api/profile/avatar`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!response.ok) throw new AuthError(response.status);
}
export function useAccount() {
  return useQuery<Account | null>({
    queryKey: ["auth", "me"],
    enabled: typeof window !== "undefined",
    initialData: null,
    retry: false,
    staleTime: 0,
    queryFn: async ({ signal }) => {
      const response = await fetch(`${base}/api/auth/me`, { credentials: "include", signal });
      if (response.status === 401) return null;
      if (!response.ok) throw new AuthError(response.status);
      return response.json() as Promise<Account>;
    },
  });
}

export function avatarUrl(account: Pick<Account, "avatar_updated_at">) {
  if (!account.avatar_updated_at) return null;
  return `${base}/api/profile/avatar?v=${encodeURIComponent(account.avatar_updated_at)}`;
}
