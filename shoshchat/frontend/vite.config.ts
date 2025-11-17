import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },

  // Build optimizations
  build: {
    // Target modern browsers for smaller bundles
    target: "es2020",

    // Output directory
    outDir: "dist",

    // Generate sourcemaps for production debugging
    sourcemap: mode === "production" ? "hidden" : true,

    // Minification settings
    minify: "terser",
    terserOptions: {
      compress: {
        // Remove console.* calls in production
        drop_console: mode === "production",
        drop_debugger: true,
        pure_funcs: mode === "production" ? ["console.log", "console.info"] : [],
      },
      mangle: {
        // Mangle variable names for smaller bundle
        safari10: true,
      },
    },

    // Rollup-specific options
    rollupOptions: {
      output: {
        // Manual chunking strategy for optimal code splitting
        manualChunks: {
          // Vendor chunks
          "react-vendor": ["react", "react-dom", "react-router-dom"],
          "ui-vendor": [
            "@radix-ui/react-alert-dialog",
            "@radix-ui/react-avatar",
            "@radix-ui/react-dialog",
            "@radix-ui/react-dropdown-menu",
            "@radix-ui/react-label",
            "@radix-ui/react-popover",
            "@radix-ui/react-select",
            "@radix-ui/react-separator",
            "@radix-ui/react-slot",
            "@radix-ui/react-tabs",
            "@radix-ui/react-toast",
          ],
          "query-vendor": ["@tanstack/react-query"],
          "state-vendor": ["zustand"],
          "charts-vendor": ["recharts"],
          "utils-vendor": ["date-fns", "clsx", "tailwind-merge"],
        },
        // Chunk file naming
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]",
      },
    },

    // Chunk size warning limit (500 KB)
    chunkSizeWarningLimit: 500,

    // CSS code splitting
    cssCodeSplit: true,

    // Report compressed size (can be slow for large bundles)
    reportCompressedSize: true,
  },

  // Development server
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: false, // Disabled for production deployment
    proxy: {
      "/api": "http://shoshchat_web:8000"
    }
  },

  // Preview server (for testing production build)
  preview: {
    port: 4173,
    host: true,
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-router-dom",
      "@tanstack/react-query",
      "zustand",
    ],
    exclude: ["@vite/client", "@vite/env"],
  },

  // Performance settings
  esbuild: {
    // Use esbuild for faster builds
    logOverride: { "this-is-undefined-in-esm": "silent" },
  },
}));
