/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F4FD',
          100: '#D1E9FB',
          200: '#A3D3F7',
          300: '#75BDF3',
          400: '#47A7EF',
          500: '#2196F3',
          600: '#1A78C2',
          700: '#145A92',
          800: '#0D3C61',
          900: '#071E31',
        },
        success: {
          50: '#E8F5E9',
          500: '#4CAF50',
          600: '#43A047',
        },
        medical: {
          light: '#E8F4FD',
          DEFAULT: '#2196F3',
          dark: '#1565C0',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
