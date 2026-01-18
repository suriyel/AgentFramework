/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neo-Swiss Color Palette
        primary: {
          DEFAULT: '#A78BFA', // Lavender purple
          light: '#C4B5FD',
          dark: '#8B5CF6',
        },
        accent: {
          DEFAULT: '#60A5FA', // Sky blue
          light: '#93C5FD',
          dark: '#3B82F6',
        },
        success: {
          DEFAULT: '#34D399', // Mint green
          light: '#6EE7B7',
          dark: '#10B981',
        },
        destructive: {
          DEFAULT: '#F87171', // Coral red
          light: '#FCA5A5',
          dark: '#EF4444',
        },
        background: '#FAFAFA',
        foreground: '#1F2937',
        muted: {
          DEFAULT: '#9CA3AF',
          foreground: '#6B7280',
        },
        border: '#E5E7EB',
        info: '#60A5FA',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
