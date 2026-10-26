import { expect, test } from '@playwright/test'
import path from 'node:path'

test('viewer loads canonical assets and controls respond', async ({ page }, testInfo) => {
  const errors: string[] = []
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()) })
  await page.goto('./')
  await expect(page.getByRole('heading', { name: '低多边形未来庭院' })).toBeVisible()
  await expect(page.locator('canvas')).toBeVisible({ timeout: 20_000 })
  await expect(page.locator('.loading')).toBeHidden({ timeout: 20_000 })
  await page.getByRole('button', { name: 'Walk' }).click()
  await expect(page.getByRole('button', { name: 'Walk' })).toHaveClass(/active/)
  await page.getByRole('button', { name: /切换夜景/ }).click()
  await expect(page.getByRole('button', { name: /切换白昼/ })).toBeVisible()
  await page.getByRole('button', { name: /配色/ }).click()
  await page.waitForTimeout(750)
  await page.screenshot({ path: path.join(process.env.AI3D_SCREENSHOT_DIR || '../evidence/screenshots', `web-${testInfo.project.name}.png`), fullPage: true })
  expect(errors).toEqual([])
})

test('static fallback works without WebGL', async ({ page }) => {
  await page.goto('./?forceFallback=1')
  await expect(page.getByAltText('未来庭院静态预览')).toBeVisible()
})

test('mobile layout has no horizontal overflow', async ({ page }) => {
  await page.goto('./?forceFallback=1')
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)
  expect(overflow).toBe(false)
})
