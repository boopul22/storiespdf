// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  site: 'https://storiespdf.com',
  integrations: [mdx(), sitemap()],

  build: {
    // Inline all CSS to eliminate render-blocking requests
    inlineStylesheets: 'always',
  },

  vite: {
    plugins: [tailwindcss()],
  },
});