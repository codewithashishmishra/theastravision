import { resolve } from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/embed.ts'),
      name: 'AastraaJobBoard',
      fileName: () => 'embed.js',
      formats: ['iife'],
    },
    outDir: 'dist',
    emptyOutDir: true,
  },
});
