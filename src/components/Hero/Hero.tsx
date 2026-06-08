import { motion, useScroll, useTransform } from 'framer-motion';
import { ArrowRight, BookOpen } from 'lucide-react';
import { useRef } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { assetUrl } from '../../utils/assetUrl';

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
  const heroBackgroundSrc = isDark ? assetUrl('/mainpage-dark.png') : assetUrl('/mainpage-light.png');

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
          src={heroBackgroundSrc}
          alt="Историческая карта России"
          className="absolute inset-0 w-full h-full object-cover object-center brightness-110"
          onError={(event) => {
            const fallback = assetUrl('/mainpage.png');
            if (event.currentTarget.getAttribute('src') !== fallback) {
              event.currentTarget.setAttribute('src', fallback);
            }
          }}
        />

        {isDark ? (
          <>
            {/* Dark: vignette edges + strong central dimming zone */}
            <div className="absolute inset-0 vignette" />
            <div className="absolute inset-0 bg-gradient-to-b from-graphite-950/74 via-graphite-950/54 to-graphite-950/96" />
            {/* Central radial shadow so map details still peek through at edges */}
            <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 75% 65% at 50% 48%, rgba(10,10,10,0.60) 0%, transparent 100%)' }} />
          </>
        ) : (
          <>
            {/* Light: strong white-cream central glow + heavy bottom fade */}
            <div className="absolute inset-0 bg-gradient-to-b from-lightBg/70 via-lightBg/35 to-lightBg/94" />
            <div className="absolute inset-0 bg-gradient-to-t from-lightBg/84 via-transparent to-lightBg/55" />
            {/* Cream radial overlay to brighten the text area */}
            <div className="absolute inset-0" style={{ background: 'radial-gradient(ellipse 75% 65% at 50% 48%, rgba(248,245,240,0.78) 0%, transparent 100%)' }} />
          </>
        )}
      </motion.div>

      {/* Content */}
      {isDark ? (
        <motion.div
          style={{ opacity }}
          className="relative z-10 section-container w-full pt-28 sm:pt-32 lg:pt-36 pb-14"
        >
          <div className="max-w-2xl">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="text-[13px] sm:text-sm font-semibold tracking-[0.16em] uppercase text-gold-400/90"
            >
              Цифровой атлас градостроительной памяти
            </motion.p>

            <motion.div
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-3 mb-8 h-px w-28 bg-gold-500/35 origin-left"
            />

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.25 }}
              className="font-serif text-5xl sm:text-6xl lg:text-7xl text-ivory-50 leading-[0.96] hero-text-shadow"
            >
              Антология
              <br />
              «Исторические города&nbsp;и&nbsp;сёла
              <br />
              России»
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.35 }}
              className="mt-7 text-lg sm:text-xl text-ivory-200/90 leading-relaxed max-w-xl hero-text-shadow"
            >
              Многотомное издание о городах, сёлах, архитектуре и пространственной памяти России.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
              className="mt-10 flex flex-wrap items-end gap-x-10 gap-y-5"
            >
              <div>
                <div className="font-serif text-5xl text-gold-400">10</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-ivory-300/80">томов</div>
              </div>
              <div className="h-14 w-px bg-gold-500/30" />
              <div>
                <div className="font-serif text-5xl text-gold-400">13</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-ivory-300/80">книг</div>
              </div>
              <div className="h-14 w-px bg-gold-500/30" />
              <div>
                <div className="font-serif text-5xl text-gold-400">6200+</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-ivory-300/80">исторических населенных пунктов</div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.55 }}
              className="mt-10 flex flex-wrap items-center gap-6"
            >
              <a
                href="#request-form"
                className="inline-flex items-center gap-2 rounded-sm bg-gold-500 px-7 py-4 text-base font-semibold text-graphite-950 transition-all duration-300 hover:bg-gold-400 hover:shadow-lg"
              >
                <BookOpen size={18} />
                Запросить электронную копию
              </a>

              <a
                href="#about"
                className="inline-flex items-center gap-2 border-b border-ivory-100/30 px-1 py-3 text-base font-semibold text-ivory-100 transition-colors duration-300 hover:border-gold-400 hover:text-gold-300"
              >
                О проекте
                <ArrowRight size={18} />
              </a>
            </motion.div>
          </div>
        </motion.div>
      ) : (
        <motion.div
          style={{ opacity }}
          className="relative z-10 section-container w-full pt-28 sm:pt-32 lg:pt-36 pb-14"
        >
          <div className="max-w-2xl">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
              className="text-[13px] sm:text-sm font-semibold tracking-[0.16em] uppercase text-gold-800/85"
            >
              Цифровой атлас градостроительной памяти
            </motion.p>

            <motion.div
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mt-3 mb-8 h-px w-28 bg-gold-700/35 origin-left"
            />

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.25 }}
              className="font-serif text-5xl sm:text-6xl lg:text-7xl text-graphite-900 leading-[0.96]"
            >
              Антология
              <br />
              «Исторические города&nbsp;и&nbsp;сёла
              <br />
              России»
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.35 }}
              className="mt-7 text-lg sm:text-xl text-lightTextSecondary leading-relaxed max-w-xl"
            >
              Многотомное издание о городах, сёлах, архитектуре и пространственной памяти России.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
              className="mt-10 flex flex-wrap items-end gap-x-10 gap-y-5"
            >
              <div>
                <div className="font-serif text-5xl text-gold-800">10</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-lightTextSecondary/90">томов</div>
              </div>
              <div className="h-14 w-px bg-gold-700/25" />
              <div>
                <div className="font-serif text-5xl text-gold-800">13</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-lightTextSecondary/90">книг</div>
              </div>
              <div className="h-14 w-px bg-gold-700/25" />
              <div>
                <div className="font-serif text-5xl text-gold-800">6200+</div>
                <div className="mt-1 text-sm uppercase tracking-[0.11em] text-lightTextSecondary/90">исторических населенных пунктов</div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.55 }}
              className="mt-10 flex flex-wrap items-center gap-6"
            >
              <a
                href="#request-form"
                className="inline-flex items-center gap-2 rounded-sm bg-gold-700 px-7 py-4 text-base font-semibold text-ivory-50 transition-all duration-300 hover:bg-gold-600 hover:shadow-lg"
              >
                <BookOpen size={18} />
                Запросить электронную копию
              </a>

              <a
                href="#about"
                className="inline-flex items-center gap-2 border-b border-graphite-900/25 px-1 py-3 text-base font-semibold text-graphite-900 transition-colors duration-300 hover:border-gold-700 hover:text-gold-800"
              >
                О проекте
                <ArrowRight size={18} />
              </a>
            </motion.div>
          </div>
        </motion.div>
      )}

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
