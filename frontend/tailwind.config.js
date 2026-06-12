/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
      colors: {
        violet: {
          50: '#EAE7FD',
          100: '#D5CEFB',
          500: '#5B4FE8',
          600: '#4A3FD6',
          700: '#3A31B8',
        },
      },
    },
  },
  plugins: [],
}
