<<<<<<< HEAD
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
=======
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1e40af', // Deep blue
          '100': '#e0e8f9',
          '600': '#1c3faa',
          '700': '#1a3baa',
        },
        accent: {
          DEFAULT: '#f97316', // Orange
          'hover': '#fb8532',
        },
        success: '#10b981', // Green
        warning: '#f59e0b', // Amber
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

>>>>>>> 97953c3 (Initial commit from Specify template)
