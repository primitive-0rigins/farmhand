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
