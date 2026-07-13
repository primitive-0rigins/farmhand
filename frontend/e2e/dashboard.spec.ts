import { expect, test } from "@playwright/test";

test("public dashboard supports manual task review", async ({ page }) => {
  await page.route("**/today", (route) => route.fulfill({
    json: {
      farm: { name: "Demo Farm", city: "Greenville", state: "SC", planting_zone: "8b" },
      today: "2026-06-26",
      forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 },
      tasks: [],
      week: [],
    },
  }));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Today on the farm" })).toBeVisible();
  await page.getByRole("button", { name: "Add task" }).click();
  await page.getByLabel("Task name").fill("Check row cover");
  await page.getByRole("button", { name: "Save task" }).click();
  await expect(page.getByText("Check row cover")).toBeVisible();
  await page.getByRole("button", { name: "Done" }).last().click();
  await expect(page.getByRole("heading", { name: "Completed" })).toBeVisible();
});

test("farmer can sign in and create a first farm", async ({ page }) => {
  await page.route("**/today", (route) => route.fulfill({ json: { farm: { name: "Demo Farm", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [], week: [] } }));
  await page.route("**/auth/request", (route) => route.fulfill({ json: { status: "sent", dev_login_token: "login-token" } }));
  await page.route("**/auth/verify", (route) => route.fulfill({ json: { session_token: "session-token" } }));
  await page.route("**/farms/7", (route) => route.fulfill({ json: { playbooks: [], assets: [], spaces: [], plantings: [] } }));
  await page.route("**/farms/7/today", (route) => route.fulfill({ json: { farm: { name: "South Field", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [], week: [] } }));
  await page.route("**/farms", async (route) => {
    if (route.request().method() === "POST") return route.fulfill({ json: { id: 7, name: "South Field" } });
    return route.fulfill({ json: [] });
  });
  await page.goto("/");
  await page.getByLabel("Use your farm").fill("farmer@example.com");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("button", { name: "Create your first farm" }).click();
  const form = page.getByLabel("Create your first farm");
  await form.getByLabel("Farm name").fill("South Field");
  await form.getByLabel("City").fill("Greenville");
  await form.getByLabel("State").fill("SC");
  await form.getByLabel("Planting zone").fill("8b");
  await form.getByRole("button", { name: "Save farm" }).click();
  await expect(page.getByText("Using your farm")).toBeVisible();
});
