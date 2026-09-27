import { defineConfig } from 'astro/config';
export default defineConfig({ output: 'static', outDir:process.env.OUT_DIR || './dist', site: process.env.SITE_URL || 'https://yuhanlydia.github.io', base: process.env.BASE_PATH || '/', trailingSlash: 'always', devToolbar: { enabled: false } });
