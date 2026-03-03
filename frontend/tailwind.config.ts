/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        kip: {
          navy:            '#0A1628',
          navymid:         '#0D1F3C',
          navylight:       '#162B4D',
          navyfaint:       '#1E3A5F',
          cornflower:      '#6495ED',
          cornflowerlight: '#85B3F5',
          cornflowerdark:  '#4A7BD4',
          cornflowerfaint: '#D6E6FF',
          white:    '#FFFFFF',
          offwhite: '#F0F4FF',
          light:    '#E8EFF8',
          muted:    '#6B7A99',
          charcoal: '#1A2133',
        },
        status: { up: '#22C55E', down: '#EF4444', warn: '#F59E0B' },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        body:    ['"Inter"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', '"Courier New"', 'monospace'],
      },
      backgroundImage: {
        'kip-gradient':        'linear-gradient(135deg, #0A1628 0%, #0D1F3C 50%, #162B4D 100%)',
        'cornflower-gradient': 'linear-gradient(135deg, #4A7BD4 0%, #6495ED 50%, #85B3F5 100%)',
        'neural-grid':         "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Ccircle cx='30' cy='30' r='1.5' fill='%236495ED' fill-opacity='0.12'/%3E%3Ccircle cx='0' cy='0' r='1' fill='%236495ED' fill-opacity='0.08'/%3E%3Ccircle cx='60' cy='0' r='1' fill='%236495ED' fill-opacity='0.08'/%3E%3Ccircle cx='0' cy='60' r='1' fill='%236495ED' fill-opacity='0.08'/%3E%3Ccircle cx='60' cy='60' r='1' fill='%236495ED' fill-opacity='0.08'/%3E%3Cline x1='0' y1='0' x2='30' y2='30' stroke='%236495ED' stroke-opacity='0.05' stroke-width='0.5'/%3E%3Cline x1='60' y1='0' x2='30' y2='30' stroke='%236495ED' stroke-opacity='0.05' stroke-width='0.5'/%3E%3C/svg%3E\")",
      },
      boxShadow: {
        'cornflower':  '0 0 0 2px #6495ED',
        'card':        '0 4px 24px rgba(10,22,40,0.08), 0 1px 4px rgba(10,22,40,0.04)',
        'card-hover':  '0 8px 32px rgba(10,22,40,0.14)',
        'glow':        '0 0 32px rgba(100,149,237,0.2)',
        'glow-strong': '0 0 48px rgba(100,149,237,0.35)',
        'navy':        '0 4px 20px rgba(10,22,40,0.4)',
      },
      animation: {
        'fade-up':   'fadeUp 0.5s ease forwards',
        'fade-in':   'fadeIn 0.4s ease forwards',
        'slide-in':  'slideIn 0.35s ease forwards',
        'pulse-slow':'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'float':     'float 6s ease-in-out infinite',
        'neural':    'neural 12s linear infinite',
      },
      keyframes: {
        fadeUp:  { from: { opacity:'0', transform:'translateY(16px)' }, to: { opacity:'1', transform:'translateY(0)' } },
        fadeIn:  { from: { opacity:'0' }, to: { opacity:'1' } },
        slideIn: { from: { transform:'translateX(-16px)', opacity:'0' }, to: { transform:'translateX(0)', opacity:'1' } },
        float:   { '0%,100%': { transform:'translateY(0)' }, '50%': { transform:'translateY(-6px)' } },
        neural:  { from: { backgroundPosition:'0 0' }, to: { backgroundPosition:'60px 60px' } },
      },
    },
  },
  plugins: [],
}
