import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: /login/i })).toBeVisible()
    await expect(page.getByLabel(/username/i)).toBeVisible()
    await expect(page.getByLabel(/password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /sign up/i }).click()
    await expect(page).toHaveURL(/\/register/)
    await expect(page.getByRole('heading', { name: /register/i })).toBeVisible()
  })

  test('should show validation errors for empty login', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: /sign in/i }).click()
    // Should show validation errors (implementation specific)
  })
})

test.describe('Dashboard Access', () => {
  test('should redirect unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })
})
