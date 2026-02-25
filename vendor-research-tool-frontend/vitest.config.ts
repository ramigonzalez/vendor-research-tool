import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environmentMatchGlobs: [
      ['src/components/**', 'jsdom'],
      ['src/lib/**', 'node'],
      ['src/hooks/**', 'jsdom'],
    ],
  },
})
