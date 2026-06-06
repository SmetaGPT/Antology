import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Compass, Briefcase, GraduationCap, BookMarked, MapPin, Heart } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const audiences = [
  {
    icon: Compass,
    title: 'Архитекторам и градостроителям',
    description: 'Справочник по историческим планировочным структурам и памятникам архитектуры.',
  },
  {
    icon: Briefcase,
    title: 'Проектировщикам и инженерам',
    description: 'Исторический контекст для проектных и реставрационных работ.',
  },
  {
    icon: GraduationCap,
    title: 'Преподавателям и студентам',
    description: 'Материал для изучения российской истории, архитектуры и градостроительства.',
  },
  {
    icon: BookMarked,
    title: 'Краеведам, музеям и библиотекам',
    description: 'Систематизированное описание исторических населённых пунктов.',
  },
  {
    icon: MapPin,
    title: 'Туристическим и культурным проектам',
    description: 'Основа для маршрутов, экскурсий и познавательных программ.',
  },
  {
    icon: Heart,
    title: 'Всем, кто интересуется историей России',
    description: 'Увлекательное путешествие по историческим городам и сёлам страны.',
  },
];

export function Audience() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, sectionBg, textPrimary } = useThemeStyles();

  return (
    <section
      id="audience"
      ref={containerRef}
      className={`section-padding ${sectionBg} relative transition-colors duration-500`}
    >
      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Аудитория</span>
          <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
            Для кого эта Антология
          </h2>
          <p className={`max-w-2xl mx-auto ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
            Издание будет полезно всем, кто профессионально или по личному интересу
            обращается к историко-архитектурному наследию России
          </p>
          <div className="gold-divider mx-auto mt-6" />
        </motion.div>

        {/* Audience Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {audiences.map((audience, index) => {
            const Icon = audience.icon;
            return (
              <motion.div
                key={audience.title}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.08 }}
                className={`card-museum group transition-all duration-300 ${isDark ? 'bg-graphite-900/50 border-ivory-100/10 hover:border-gold-500/30 hover:shadow-museum' : 'bg-lightBgSecondary/70 border-lightBorder hover:border-gold-400/50 hover:shadow-light-shadow'}`}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="flex-shrink-0">
                    <div className={`w-12 h-12 border rounded-sm flex items-center justify-center transition-all duration-300 ${isDark ? 'border-gold-500/30 group-hover:border-gold-400 group-hover:bg-gold-500/10' : 'border-gold-400/40 group-hover:border-gold-600 group-hover:bg-gold-100/20'}`}>
                      <Icon className={`w-6 h-6 transition-colors ${isDark ? 'text-gold-400/80 group-hover:text-gold-400' : 'text-gold-600/80 group-hover:text-gold-700'}`} />
                    </div>
                  </div>

                  {/* Content */}
                  <div>
                    <h3 className={`font-serif text-lg mb-2 transition-colors ${isDark ? 'text-ivory-50 group-hover:text-gold-400' : 'text-lightText group-hover:text-gold-600'}`}>
                      {audience.title}
                    </h3>
                    <p className={`text-sm leading-relaxed ${isDark ? 'text-ivory-300/60' : 'text-lightTextSecondary'}`}>
                      {audience.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
