import { test } from "node:test";
import assert from "node:assert/strict";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToStaticMarkup } from "react-dom/server";
import { PageIntro } from "../src/components/layout/page-intro";

test("Page intros keep their assigned photo when album backgrounds are active", () => {
  const queryClient = new QueryClient();
  queryClient.setQueryData(["media", "backgrounds"], {
    album_id: "album-1",
    interval_seconds: 8,
    transition: "fade",
    photos: [{ id: "photo-1", url: "/api/media/photos/photo-1/content" }],
  });
  const html = renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <PageIntro title="The squad" backgroundImage="/static/squad.jpg" />
    </QueryClientProvider>,
  );
  assert.ok(html.includes("/static/squad.jpg"));
  assert.ok(!html.includes("/api/media/photos/photo-1/content"));
});
