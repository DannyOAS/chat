module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        retail: {
          primary: "#ff6b6b",
          accent: "#ffe66d"
        },
        finance: {
          primary: "#1a535c",
          accent: "#4ecdc4"
        }
      }
    }
  },
  plugins: []
};
