import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const stats = [
  { number: '10', label: 'томов', suffix: '' },
  { number: '13', label: 'книг', suffix: '' },
  { number: '6200+', label: 'городов и сёл', suffix: '' },
  {
    number: '100+',
    label: 'авторских\nисследований',
    suffix: '',
    labelClassName: 'whitespace-pre-line leading-tight max-w-[9rem] mx-auto',
  },
  {
    number: 'Россия',
    label: 'от края до края',
    suffix: '',
    numberClassName: 'text-4xl md:text-5xl lg:text-6xl whitespace-nowrap',
    labelClassName: 'max-w-[11rem] mx-auto leading-tight',
  },
];

export function Statistics() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark } = useThemeStyles();

  return (
    <section
      ref={containerRef}
      className={`py-20 md:py-28 ${isDark ? 'bg-gradient-to-b from-graphite-950 via-graphite-900/50 to-graphite-950' : 'bg-gradient-to-b from-lightBg via-lightBgSecondary/30 to-lightBg'} relative overflow-hidden transition-colors duration-500`}
    >
      {/* Decorative lines */}
      <div className={`absolute top-0 left-0 w-full gold-line ${isDark ? 'from-gold-600/0 via-gold-500/50 to-gold-600/0' : 'from-gold-500/0 via-gold-400/30 to-gold-500/0'}`} />
      <div className={`absolute bottom-0 left-0 w-full gold-line ${isDark ? 'from-gold-600/0 via-gold-500/50 to-gold-600/0' : 'from-gold-500/0 via-gold-400/30 to-gold-500/0'}`} />

      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Масштаб издания</span>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 lg:gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className={`card-museum text-center group relative ${isDark ? 'bg-graphite-900/50 border-ivory-100/10 hover:border-gold-500/30 hover:shadow-museum' : 'bg-lightBgSecondary/70 border-lightBorder hover:border-gold-400/50 hover:shadow-light-shadow'} transition-all duration-300`}
            >
              {/* Decorative frame corner */}
              <div className={`absolute top-0 left-0 w-4 h-4 border-t border-l ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />
              <div className={`absolute top-0 right-0 w-4 h-4 border-t border-r ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />
              <div className={`absolute bottom-0 left-0 w-4 h-4 border-b border-l ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />
              <div className={`absolute bottom-0 right-0 w-4 h-4 border-b border-r ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />

              <motion.span
                initial={{ opacity: 0, scale: 0.5 }}
                animate={isInView ? { opacity: 1, scale: 1 } : {}}
                transition={{ duration: 0.6, delay: index * 0.1 + 0.2 }}
                className={`stat-number block mb-2 transition-colors ${stat.numberClassName ?? ''} ${isDark ? 'group-hover:text-gold-300' : 'group-hover:text-gold-800'}`}
              >
                {stat.number}
              </motion.span>
              <span className={`block text-sm tracking-wide uppercase ${stat.labelClassName ?? ''} ${isDark ? 'text-ivory-400/80' : 'text-lightTextSecondary'}`}>
                {stat.label}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
