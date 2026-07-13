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

test("farmer can correct a saved planting", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("farmhand-session-token", "session-token");
    localStorage.setItem("farmhand-farm-id", "7");
  });
  await page.route("**/farms/7/plantings/3", async (route) => {
    expect(route.request().method()).toBe("PUT");
    expect(route.request().postDataJSON()).toEqual({ crop: "lettuce", planted_on: "2026-04-05", succession_interval_days: 14 });
    await route.fulfill({ json: { id: 3, crop: "lettuce", planted_on: "2026-04-05", succession_interval_days: 14 } });
  });
  await page.route("**/farms/7/today", (route) => route.fulfill({ json: { farm: { name: "South Field", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [], week: [] } }));
  await page.route("**/farms/7", (route) => route.fulfill({ json: { playbooks: [], assets: [], spaces: [], plantings: [{ id: 3, crop: "lettuce", planted_on: "2026-04-01", succession_interval_days: null }] } }));
  await page.route("**/farms", (route) => route.fulfill({ json: [{ id: 7, name: "South Field" }] }));
  await page.goto("/");
  await page.getByRole("button", { name: "Manage setup" }).click();
  await page.getByRole("button", { name: "Edit" }).click();
  const setup = page.getByLabel("Farm setup");
  await setup.getByLabel("Planted on").fill("2026-04-05");
  await setup.getByLabel("Succession interval (days)").fill("14");
  await setup.getByRole("button", { name: "Save" }).click();
  await expect(setup.getByText("every 14 days")).toBeVisible();
});

test("farmer can add equipment from farm setup", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("farmhand-session-token", "session-token");
    localStorage.setItem("farmhand-farm-id", "7");
  });
  await page.route("**/farms/7/assets", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toEqual({ name: "West drip", kind: "irrigation" });
    await route.fulfill({ json: { id: 4, name: "West drip", kind: "irrigation" } });
  });
  await page.route("**/farms/7/today", (route) => route.fulfill({ json: { farm: { name: "South Field", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [], week: [] } }));
  await page.route("**/farms/7", (route) => route.fulfill({ json: { playbooks: [], assets: [], spaces: [], plantings: [] } }));
  await page.route("**/farms", (route) => route.fulfill({ json: [{ id: 7, name: "South Field" }] }));
  await page.goto("/");
  await page.getByRole("button", { name: "Manage setup" }).click();
  await page.getByRole("button", { name: "Add equipment" }).click();
  const form = page.getByLabel("Add equipment");
  await form.getByLabel("Name").fill("West drip");
  await form.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("West drip (irrigation)")).toBeVisible();
});

test("farmer can save a manual task to their farm", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("farmhand-session-token", "session-token");
    localStorage.setItem("farmhand-farm-id", "7");
  });
  await page.route("**/farms/7/manual-tasks", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toEqual({ title: "Check row cover", reason: "Created manually for today's work.", due_date: "2026-06-26" });
    await route.fulfill({ json: { id: 8, title: "Check row cover", reason: "Created manually for today's work.", due_date: "2026-06-26" } });
  });
  await page.route("**/farms/7/today", (route) => route.fulfill({ json: { farm: { name: "South Field", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [], week: [] } }));
  await page.route("**/farms/7", (route) => route.fulfill({ json: { playbooks: [], assets: [], spaces: [], plantings: [] } }));
  await page.route("**/farms", (route) => route.fulfill({ json: [{ id: 7, name: "South Field" }] }));
  await page.goto("/");
  await page.getByRole("button", { name: "Add task" }).click();
  await page.getByLabel("Task name").fill("Check row cover");
  await page.getByRole("button", { name: "Save task" }).click();
  await expect(page.getByText("Check row cover")).toBeVisible();
});

test("farmer can remove a saved manual task", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("farmhand-session-token", "session-token");
    localStorage.setItem("farmhand-farm-id", "7");
  });
  await page.route("**/farms/7/manual-tasks/8", async (route) => {
    expect(route.request().method()).toBe("DELETE");
    await route.fulfill({ status: 204 });
  });
  await page.route("**/farms/7/today", (route) => route.fulfill({ json: { farm: { name: "South Field", city: "Greenville", state: "SC", planting_zone: "8b" }, today: "2026-06-26", forecast: { date: "2026-06-27", summary: "Storms tomorrow", thunderstorm_risk: true, high_wind_mph: 34, heat_index_f: 91 }, tasks: [{ id: "manual-8", title: "Check row cover", due_date: "2026-06-26", severity: "info", reason: "Manual work.", steps: [], source_rule: null, status: "open" }], week: [] } }));
  await page.route("**/farms/7", (route) => route.fulfill({ json: { playbooks: [], assets: [], spaces: [], plantings: [] } }));
  await page.route("**/farms", (route) => route.fulfill({ json: [{ id: 7, name: "South Field" }] }));
  await page.goto("/");
  await page.getByRole("button", { name: "Remove" }).click();
  await expect(page.getByText("Today is clear.")).toBeVisible();
});
