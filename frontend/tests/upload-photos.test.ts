import { test } from "node:test";
import assert from "node:assert/strict";
import { PhotoUploadError, uploadPhotos } from "../src/features/gallery/upload-photos";

test("a partial upload retries only unfinished photos on the same parent", async () => {
  const originalFetch = globalThis.fetch;
  let pending = ["first.png", "second.png", "third.png"].map(
    (name) => new File(["image"], name, { type: "image/png" }),
  );
  const sent: string[] = [];
  let fail = true;
  globalThis.fetch = (async (url, init) => {
    assert.equal(url, "/api/media/albums/saved-album/photos");
    const file = init?.body as File;
    sent.push(file.name);
    return fail && file.name === "second.png"
      ? new Response(null, { status: 503 })
      : Response.json({ id: file.name });
  }) as typeof fetch;
  try {
    const complete = () => {
      pending = pending.slice(1);
    };
    await assert.rejects(
      uploadPhotos("/albums/saved-album/photos", pending, complete),
      (error: unknown) => error instanceof PhotoUploadError && error.fileName === "second.png",
    );
    assert.deepEqual(
      pending.map((file) => file.name),
      ["second.png", "third.png"],
    );
    fail = false;
    await uploadPhotos("/albums/saved-album/photos", pending, complete);
    assert.deepEqual(sent, ["first.png", "second.png", "second.png", "third.png"]);
    assert.deepEqual(pending, []);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
