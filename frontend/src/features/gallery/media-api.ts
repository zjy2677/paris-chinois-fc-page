import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");

export type Photo = { id: string; url: string; caption: string | null; alt_text: string };
export type Album = {
  id: string;
  title: string;
  description: string | null;
  event_date: string | null;
  created_at: string;
  photos: Photo[];
};

export function mediaUrl(url: string) {
  return url.startsWith("http") ? url : `${base}${url}`;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}/api/media${path}`, {
    credentials: "include",
    ...init,
    ...(init?.body && typeof init.body === "string"
      ? { headers: { "Content-Type": "application/json" } }
      : {}),
  });
  if (!response.ok) throw new Error(`Media request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export async function uploadPhoto(
  path: string,
  file: File,
  fields?: { caption?: string; alt?: string },
) {
  const query = new URLSearchParams();
  if (fields?.caption) query.set("caption", fields.caption);
  if (fields?.alt) query.set("alt", fields.alt);
  const suffix = query.size ? `?${query}` : "";
  const response = await fetch(`${base}/api/media${path}${suffix}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!response.ok) throw new Error(`Photo upload failed: ${response.status}`);
  return response.json() as Promise<Photo>;
}

export function useAlbums() {
  return useQuery({ queryKey: ["media", "albums"], queryFn: () => json<Album[]>("/albums") });
}

export function useCreateAlbum() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; description: string | null; event_date: string | null }) =>
      json<Album>("/albums", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => void cache.invalidateQueries({ queryKey: ["media", "albums"] }),
  });
}
