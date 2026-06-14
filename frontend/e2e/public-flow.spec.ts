import { expect, test } from '@playwright/test'

test('visitor can open the authentication flow', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/LinguaLeap/i)
  await page.getByRole('link', { name: /start learning|get started/i }).first().click()
  await expect(page).toHaveURL(/\/auth/)
  await expect(page.getByRole('heading', { name: /create your learner profile/i })).toBeVisible()
})
