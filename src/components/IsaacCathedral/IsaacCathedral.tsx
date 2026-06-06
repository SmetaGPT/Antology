import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ImagePlaceholder } from '../ui/ImagePlaceholder';
import { Users, Award, BookOpen } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const features = [
  {
    icon: Users,
    title: 'Профессиональное сообщество',
    description: 'Архитекторы и градостроители, учёные и эксперты',
  },
  {
    icon: Award,
    title: 'Культурное событие',
    description: 'Презентация значимого издания в музее-памятнике',
  },
  {
    icon: BookOpen,
    title: 'Передача книжного комплекта',
    description: 'Официальное вручение издания в фонды музея',
  },
];

export function IsaacCathedral() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, textPrimary, accentGold } = useThemeStyles();

  return (
    <section
      ref={containerRef}
      className={`section-padding ${isDark ? 'bg-graphite-900' : 'bg-lightBgSecondary'} relative overflow-hidden transition-colors duration-500`}
    >
      {/* Dark/Light overlay pattern */}
      <div className={`absolute inset-0 bg-gradient-radial ${isDark ? 'from-graphite-800/50 via-graphite-900 to-graphite-950' : 'from-lightBorder/30 via-lightBgSecondary to-lightBg'}`} />

      {/* Gold decorative frame */}
      <div className={`absolute inset-8 border pointer-events-none hidden lg:block ${isDark ? 'border-gold-500/10' : 'border-gold-400/10'}`} />

      <div className="section-container relative">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center"
        >
          {/* Image */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="relative">
              {/* Decorative frame */}
              <div className={`absolute -inset-4 border rounded-sm ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />

              <ImagePlaceholder
                src="/images/isaac-cathedral-ceremony.jpg"
                alt="Исаакиевский собор в Санкт-Петербурге"
                aspectRatio="wide"
                className="rounded-sm"
                overlayText="Исаакиевский собор"
              />

              {/* Overlay gradient */}
              <div className={`absolute inset-0 rounded-sm bg-gradient-to-t ${isDark ? 'from-graphite-900/80 via-transparent to-transparent' : 'from-lightBgSecondary/60 via-transparent to-transparent'}`} />
            </div>
          </motion.div>

          {/* Content */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Официальная презентация</span>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.4 }}
              className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6 leading-tight`}
            >
              Антология, представленная в стенах{' '}
              <span className={accentGold}>Исаакиевского собора</span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.5 }}
              className={`text-lg leading-relaxed mb-10 ${isDark ? 'text-ivory-200/80' : 'text-lightTextSecondary/80'}`}
            >
              Официальная презентация 10-томного издания прошла в Государственном музее
              «Исаакиевский собор» в Санкт-Петербурге. В мероприятии участвовали архитекторы,
              градостроители, учёные, представители профессионального и культурного сообщества.
            </motion.p>

            {/* Feature cards */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="grid sm:grid-cols-3 gap-4 mb-10"
            >
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div
                    key={feature.title}
                    className={`border rounded-sm p-4 text-center transition-colors ${isDark ? 'bg-graphite-800/50 border-ivory-100/10' : 'bg-lightBgSecondary/70 border-lightBorder'}`}
                  >
                    <Icon className={`w-6 h-6 mx-auto mb-3 ${isDark ? 'text-gold-400/80' : 'text-gold-600/80'}`} />
                    <h4 className={`text-sm font-medium mb-1 ${isDark ? 'text-ivory-100' : 'text-lightText'}`}>
                      {feature.title}
                    </h4>
                    <p className={`text-xs ${isDark ? 'text-ivory-400/60' : 'text-lightTextSecondary'}`}>{feature.description}</p>
                  </div>
                );
              })}
            </motion.div>

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.7 }}
            >
              <a href="#request-form" className="btn-primary">
                Запросить электронный доступ
              </a>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
