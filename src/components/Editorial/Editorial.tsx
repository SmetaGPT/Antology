import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { useThemeStyles } from '../../hooks/useThemeStyles';
import { assetUrl } from '../../utils/assetUrl';

export function Editorial() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, sectionBg, textPrimary } = useThemeStyles();

  return (
    <section
      id="about"
      ref={containerRef}
      className={`section-padding ${sectionBg} relative overflow-hidden transition-colors duration-500`}
    >
      {/* Background texture */}
      <div className={`absolute inset-0 opacity-5 ${isDark ? 'bg-gradient-to-br from-gold-500/10 via-transparent to-transparent' : 'bg-gradient-to-br from-gold-400/5 via-transparent to-transparent'}`} />
      <div className={`absolute inset-0 ${isDark ? 'editorial-texture-dark' : 'editorial-texture-light'}`} />

      <div className="section-container relative">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center"
        >
          {/* Text Content */}
          <div className="order-2 lg:order-1 max-w-[640px]">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <span className={`museum-label block ${isDark ? 'text-gold-400/90' : 'text-gold-800/90'}`}>
                О проекте
              </span>
              <div className={`mt-3 relative h-px w-24 ${isDark ? 'bg-gold-500/45' : 'bg-gold-700/45'}`}>
                <span className={`absolute -right-1 -top-[3px] h-1.5 w-1.5 rotate-45 ${isDark ? 'bg-gold-500/70' : 'bg-gold-700/70'}`} />
              </div>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.2 }}
              className={`font-serif text-5xl sm:text-6xl ${textPrimary} mb-8 leading-[1.02]`}
            >
              Не просто издание —
              <span className={`block ${isDark ? 'text-gold-400' : 'text-gold-700'}`}>
                архитектурная летопись
              </span>
              <span className={`block ${isDark ? 'text-gold-400' : 'text-gold-700'}`}>
                страны
              </span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.3 }}
              className={`text-lg sm:text-xl ${isDark ? 'text-ivory-200/88' : 'text-lightTextSecondary/95'} leading-relaxed mb-6`}
            >
              Антология собирает воедино историю городов и сёл России и показывает, как через
              расселение, архитектуру, планировку, храмы, крепости, улицы и площади
              формировался пространственный образ страны.
            </motion.p>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.4 }}
              className={`text-base sm:text-lg leading-relaxed ${isDark ? 'text-ivory-200/82' : 'text-lightTextSecondary/90'}`}
            >
              Это уникальное издание представляет собой историко-градостроительный атлас,
              охватывающий территорию современной России и документирующий более шести тысяч
              исторических населённых пунктов, каждый из которых имеет свою уникальную
              историю, архитектурное наследие и градостроительную традицию.
            </motion.p>

            {/* Decorative element */}
            <motion.div
              initial={{ opacity: 0, scaleX: 0 }}
              animate={isInView ? { opacity: 1, scaleX: 1 } : {}}
              transition={{ duration: 0.8, delay: 0.5 }}
              className={`mt-9 h-px w-36 ${isDark ? 'bg-gold-500/55' : 'bg-gold-700/55'}`}
            />
          </div>

          {/* Image */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="order-1 lg:order-2"
          >
            <div className={`editorial-frame ${isDark ? 'editorial-frame-dark' : 'editorial-frame-light'}`}>
              <div className="editorial-frame-inner">
                <img
                  src={assetUrl('/razvorot.png')}
                  alt="Книжный разворот Антологии"
                  className={`h-full w-full object-contain ${isDark ? 'bg-graphite-950/65' : 'bg-white/70'}`}
                />
              </div>

              {/* Museum label */}
              <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className={`text-xs tracking-[0.16em] uppercase ${isDark ? 'text-gold-400/70' : 'text-gold-800/70'}`}>
                  •
                </span>
                <span className={`mx-3 text-xs tracking-[0.16em] uppercase ${isDark ? 'text-gold-400/70' : 'text-gold-800/70'}`}>
                  Цифровой историко-градостроительный атлас
                </span>
                <span className={`text-xs tracking-[0.16em] uppercase ${isDark ? 'text-gold-400/70' : 'text-gold-800/70'}`}>
                  •
                </span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
