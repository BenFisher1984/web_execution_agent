module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  safelist: [
    "bg-green-600",
    "bg-red-600",
    "text-white",
    "font-bold",
    "px-3",
    "py-1",
    "rounded",
    "bg-gradient-to-br",
    "from-black",
    "via-gray-900",
    "to-blue-900",
    "bg-gray-800/90",
    "text-gray-300",
    "text-gray-400",
    "border-gray-700"
  ],
  theme: {
    extend: {
      colors: {
        'dark-panel': 'rgba(31, 41, 55, 0.9)',
        'dark-input': 'rgba(55, 65, 81, 0.8)',
        'dark-border': 'rgba(75, 85, 99, 0.6)',
      },
      backgroundImage: {
        'dark-gradient': 'linear-gradient(to bottom right, #000000, #1f2937, #1e3a8a)',
      }
    },
  },
  plugins: [],
}
