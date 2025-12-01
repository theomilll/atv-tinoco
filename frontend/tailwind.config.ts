import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          dark: '#1a1a1a',
          surface: '#2a2a2a',
          elevated: '#3a3a3a',
        },
        border: '#4a4a4a',
        accent: {
          DEFAULT: '#7a8a6a',
          light: '#8b9a7b',
          dark: '#5a6a4a',
        },
        text: {
          primary: '#ffffff',
          secondary: '#b0b0b0',
          muted: '#707070',
        },
      },
      fontFamily: {
        mono: ['Departure Mono', 'monospace'],
      },
      letterSpacing: {
        brutal: '0.1em',
      },
    },
  },
  plugins: [],
}
export default config
