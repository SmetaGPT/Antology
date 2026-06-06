import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

export function Hero() {
  const { theme } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'],
  });

  const parallaxY = useTransform(scrollYProgress, [0, 1], ['0%', '30%']);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  const isDark = theme === 'dark';

  return (
    <section
      ref={containerRef}
      className={`relative min-h-screen flex items-center justify-center overflow-hidden transition-colors duration-500 ${
        isDark ? 'bg-graphite-950' : 'bg-lightBg'
      }`}
    >
      {/* Background Map with Parallax */}
      <motion.div
        style={{ y: parallaxY }}
        className="absolute inset-0 z-0"
      >
        {/* Historical map image */}
        <img
          src="/mainpage.png"
          alt="Историческая карта России"
          className="absolute inset-0 w-full h-full object-cover object-center"
        />

        {isDark ? (
          <>
            {/* Dark: vignette edges + strong central dimming zone */}
            <div className="absolute inset-0 vignette" />
            <div className="absolute inset-0 bg-gradient-to-b from-graphite-950/70 via-graphite-950/50 to-graphite-950/95" />
            {/* Central radial shadow so map details still peek through at edges */}
            <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 75% 65% at 50% 48%, rgba(10,10,10,0.55) 0%, transparent 100%)' }} />
          </>
        ) : (
          <>
            {/* Light: strong white-cream central glow + heavy bottom fade */}
            <div className="absolute inset-0 bg-gradient-to-b from-lightBg/65 via-lightBg/30 to-lightBg/92" />
            <div className="absolute inset-0 bg-gradient-to-t from-lightBg/80 via-transparent to-lightBg/50" />
            {/* Cream radial overlay to brighten the text area */}
            <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 75% 65% at 50% 48%, rgba(248,245,240,0.72) 0%, transparent 100%)' }} />
          </>
        )}
      </motion.div>

      {/* Content */}
      <motion.div
        style={{ opacity }}
        className="relative z-10 section-container text-center px-4"
      >
        {/* Main Title */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className={`font-serif text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl mb-6 leading-tight ${
            isDark ? 'hero-text-shadow' : 'hero-text-shadow-light'
          }`}
        >
          <span className={`block ${isDark ? 'text-ivory-50' : 'text-graphite-950'}`}>
            Антология
          </span>
          <span className={`block mt-2 ${isDark ? 'text-ivory-100' : 'text-gold-900'}`}>
            «Исторические города и сёла России»
          </span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className={`text-base sm:text-lg max-w-2xl mx-auto mb-10 ${
            isDark ? 'text-ivory-200 hero-text-shadow' : 'text-graphite-900 hero-text-shadow-light'
          }`}
        >
          Цифровой атлас градостроительной памяти России.
        </motion.p>

        {/* Gold Divider */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="gold-divider mx-auto mb-10"
        />

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <a href="#request-form" className="btn-primary w-full sm:w-auto">
            Запросить электронный доступ
          </a>
          <a href="#request-form" className="btn-secondary w-full sm:w-auto">
            Подать заявку на бумажный комплект
          </a>
        </motion.div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            className={`w-6 h-10 border rounded-full flex justify-center pt-2 transition-colors ${
              isDark ? 'border-ivory-300/30' : 'border-gold-700/40'
            }`}
          >
            <div
              className={`w-1 h-2 rounded-full ${
                isDark ? 'bg-gold-400/60' : 'bg-gold-700/60'
              }`}
            />
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Decorative Gold Lines */}
      <div className={`absolute top-0 left-0 w-full h-px bg-gradient-to-r ${
        isDark ? 'from-transparent via-gold-500/30 to-transparent' : 'from-transparent via-gold-600/30 to-transparent'
      }`} />
      <div className={`absolute bottom-0 left-0 w-full h-px bg-gradient-to-r ${
        isDark ? 'from-transparent via-gold-500/30 to-transparent' : 'from-transparent via-gold-600/30 to-transparent'
      }`} />
    </section>
  );
}
