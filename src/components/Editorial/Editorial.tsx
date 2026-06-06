import { motion } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { useThemeStyles } from '../../hooks/useThemeStyles';
import { ImagePlaceholder } from '../ui/ImagePlaceholder';

export function Editorial() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, sectionBg, textPrimary, textSecondary } = useThemeStyles();

  return (
    <section
      id="about"
      ref={containerRef}
      className={`section-padding ${sectionBg} relative overflow-hidden transition-colors duration-500`}
    >
      {/* Background texture */}
      <div className={`absolute inset-0 opacity-5 ${isDark ? 'bg-gradient-to-br from-gold-500/10 via-transparent to-transparent' : 'bg-gradient-to-br from-gold-400/5 via-transparent to-transparent'}`} />

      <div className="section-container relative">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center"
        >
          {/* Text Content */}
          <div className="order-2 lg:order-1">
            <motion.span
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.1 }}
              className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}
            >
              О проекте
            </motion.span>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.2 }}
              className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-8 leading-tight`}
            >
              Не просто издание —{' '}
              <span className={isDark ? 'text-gold-400' : 'text-gold-700'}>архитектурная летопись страны</span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.3 }}
              className={`text-lg ${isDark ? 'text-ivory-200/80' : 'text-lightTextSecondary/90'} leading-relaxed mb-6`}
            >
              Антология собирает воедино историю городов и сёл России и показывает, как через
              расселение, архитектуру, планировку, храмы, крепости, улицы и площади
              формировался пространственный образ страны.
            </motion.p>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.4 }}
              className={`text-base leading-relaxed ${textSecondary}`}
            >
              Это уникальное издание представляет собой историко-градостроительный атлас,
              охватывающий территорию современной России и documenting более шести тысяч
              исторических населённых пунктов, каждый из которых имеет свою уникальную
              историю, архитектурное наследие и градостроительную традицию.
            </motion.p>

            {/* Decorative element */}
            <motion.div
              initial={{ opacity: 0, scaleX: 0 }}
              animate={isInView ? { opacity: 1, scaleX: 1 } : {}}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="gold-divider mt-8"
            />
          </div>

          {/* Image */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="order-1 lg:order-2"
          >
            <div className="relative">
              {/* Frame */}
              <div className={`absolute -inset-4 border rounded-sm ${isDark ? 'border-gold-500/20' : 'border-gold-700/40'}`} />
              <div className={`absolute -inset-8 border rounded-sm ${isDark ? 'border-gold-500/10' : 'border-gold-700/20'}`} />

              <ImagePlaceholder
                src="/images/book-spread.jpg"
                alt="Книжный разворот Антологии"
                aspectRatio="portrait"
                className="rounded-sm shadow-museum"
                overlayText="Книжный разворот"
              />

              {/* Museum label */}
              <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className={`text-xs tracking-[0.15em] uppercase ${isDark ? 'text-ivory-400/50' : 'text-gold-700/60'}`}>
                  Цифровой историко-градостроительный атлас
                </span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
