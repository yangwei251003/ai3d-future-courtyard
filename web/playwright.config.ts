import { defineConfig, devices } from '@playwright/test'

const port = Number(process.env.AI3D_TEST_PORT || 4188)

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${port}${process.env.AI3D_TEST_BASE_PATH || '/'}`,
    channel: 'chrome',
    trace: 'retain-on-failure',
    launchOptions: process.env.AI3D_SOFTWARE_GL === '1' ? { args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } : {},
  },
  webServer: {
    command: 'node ../tools/serve-public.mjs',
    url: `http://127.0.0.1:${port}${process.env.AI3D_TEST_BASE_PATH || '/'}`,
    reuseExistingServer: false,
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
})
