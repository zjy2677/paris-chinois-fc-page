import { test } from "node:test";
import assert from "node:assert/strict";
import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { restorePublicQueryCache } from "../src/lib/public-query-cache";

test("blocked browser storage cannot abort query initialization", () => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "window");
  const client = new QueryClient();
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: {
      get localStorage() {
        throw new Error("Storage blocked");
      },
    },
  });
  try {
    assert.doesNotThrow(() => restorePublicQueryCache(client));
  } finally {
    client.clear();
    if (original) Object.defineProperty(globalThis, "window", original);
    else Reflect.deleteProperty(globalThis, "window");
  }
});

test("restored public queries retain data beyond default garbage collection", () => {
  const original = Object.getOwnPropertyDescriptor(globalThis, "window");
  const client = new QueryClient();
  const key = ["league", "match", "match-id"];
  const data = { id: "match-id", score: [2, 1] };
  const updatedAt = Date.now() - 10 * 60_000;
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    value: {
      localStorage: {
        getItem: () => JSON.stringify([{ queryKey: key, data, updatedAt }]),
        removeItem: () => {},
      },
    },
  });
  try {
    restorePublicQueryCache(client);
    assert.deepEqual(client.getQueryData(key), data);
    const observer = new QueryObserver(client, { queryKey: key, enabled: false });
    const unsubscribe = observer.subscribe(() => {});
    unsubscribe();
    assert.equal(client.getQueryCache().find({ queryKey: key })?.gcTime, 24 * 60 * 60_000);
    assert.equal(client.getQueryDefaults(["players", "leaderboards"]).gcTime, 24 * 60 * 60_000);
    assert.equal(client.getQueryDefaults(["account"]).gcTime, undefined);
    assert.equal(client.getQueryState(key)?.dataUpdatedAt, updatedAt);
  } finally {
    client.clear();
    if (original) Object.defineProperty(globalThis, "window", original);
    else Reflect.deleteProperty(globalThis, "window");
  }
});
