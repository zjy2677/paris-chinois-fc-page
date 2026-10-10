import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const base = (import.meta.env?.["VITE_API_BASE_URL"] ?? "").replace(/\/$/, "");

export type BackgroundTransition = "fade" | "slide" | "zoom";
export type Photo = {
  id: string;
  url: string;
  caption: string | null;
  alt_text: string;
  use_as_background: boolean;
};
export type Album = {
  id: string;
  title: string;
  description: string | null;
  event_date: string | null;
  background_enabled: boolean;
  background_interval_seconds: number;
  background_transition: BackgroundTransition;
  created_at: string;
  photos: Photo[];
};
export type Backgrounds = {
  album_id: string | null;
  interval_seconds: number;
  transition: BackgroundTransition;
  photos: Photo[];
};
export type AlbumUpdate = Pick<
  Album,
  | "title"
  | "description"
  | "event_date"
  | "background_enabled"
  | "background_interval_seconds"
  | "background_transition"
>;

export function mediaUrl(url: string) {
  return url.startsWith("http") ? url : `${base}${url}`;
}

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${base}/api/media${path}`, {
    credentials: "include",
    ...init,
    ...(init?.body && typeof init.body === "string"
      ? { headers: { "Content-Type": "application/json" } }
      : {}),
  });
  if (!response.ok) throw new Error(`Media request failed: ${response.status}`);
  return response;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init);
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

export function useBackgrounds() {
  return useQuery({
    queryKey: ["media", "backgrounds"],
    queryFn: () => json<Backgrounds>("/backgrounds"),
    staleTime: 60_000,
  });
}

export function useCreateAlbum() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; description: string | null; event_date: string | null }) =>
      json<Album>("/albums", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => void cache.invalidateQueries({ queryKey: ["media", "albums"] }),
  });
}

function useRefreshMedia() {
  const cache = useQueryClient();
  return () => {
    void cache.invalidateQueries({ queryKey: ["media", "albums"] });
    void cache.invalidateQueries({ queryKey: ["media", "backgrounds"] });
  };
}

export function useUpdateAlbum() {
  const refresh = useRefreshMedia();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AlbumUpdate }) =>
      json<Album>(`/albums/${encodeURIComponent(id)}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: refresh,
  });
}

export function useDeleteAlbum() {
  const refresh = useRefreshMedia();
  return useMutation({
    mutationFn: (id: string) => request(`/albums/${encodeURIComponent(id)}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
}

export function useUpdateAlbumPhoto() {
  const refresh = useRefreshMedia();
  return useMutation({
    mutationFn: ({
      albumId,
      photoId,
      selected,
    }: {
      albumId: string;
      photoId: string;
      selected: boolean;
    }) =>
      json<Photo>(`/albums/${encodeURIComponent(albumId)}/photos/${encodeURIComponent(photoId)}`, {
        method: "PATCH",
        body: JSON.stringify({ use_as_background: selected }),
      }),
    onSuccess: refresh,
  });
}

export function useDeletePhoto() {
  const refresh = useRefreshMedia();
  return useMutation({
    mutationFn: (photoId: string) =>
      request(`/photos/${encodeURIComponent(photoId)}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
}
