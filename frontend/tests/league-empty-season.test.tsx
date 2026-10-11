import { test } from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nProvider } from "../src/i18n/i18n-provider";
import { LeaguePage } from "../src/features/league/league-page";
import type { Account } from "../src/features/auth/auth-api";

const account: Account = {
  id: "account-id",
  email: "admin@example.test",
  first_name: null,
  last_name: null,
  age_at_registration: null,
  role: "admin",
  avatar_updated_at: null,
};

function renderLeaguePage(role: Account["role"]) {
  const client = new QueryClient();
  client.setQueryData(["auth", "me"], { ...account, role });
  client.setQueryData(["league", "seasons"], []);
  try {
    return renderToStaticMarkup(
      <QueryClientProvider client={client}>
        <I18nProvider>
          <LeaguePage />
        </I18nProvider>
      </QueryClientProvider>,
    );
  } finally {
    client.clear();
  }
}

test("an admin can create the first match before any seasons exist", () => {
  const markup = renderLeaguePage("admin");
  assert.match(markup, /Create a match/);
  assert.match(markup, /No seasons available yet/);
});

test("an ordinary user cannot create a match when no seasons exist", () => {
  const markup = renderLeaguePage("user");
  assert.doesNotMatch(markup, /Create a match/);
  assert.match(markup, /No seasons available yet/);
});
