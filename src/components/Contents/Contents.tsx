import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Building2, Castle, Map, ScrollText, Globe } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const contents = [
  {
    icon: Building2,
    title: 'Исторические города',
    description: 'Подробные описания более 300 исторических городов России с архитектурным и градостроительным анализом.',
  },
  {
    icon: Castle,
    title: 'Исторические сёла',
    description: 'Сведения о тысячи исторических сёл и деревень, их происхождении, планировке и культурном наследии.',
  },
  {
    icon: Map,
    title: 'Архитектура и планировка',
    description: 'Градостроительные характеристики, типы планировочной структуры, историческая застройка и памятники.',
  },
  {
    icon: ScrollText,
    title: 'Гербы, планы, документы',
    description: 'Геральдика городов, старинные планы, карты, архивные материалы и исторические документы.',
  },
  {
    icon: Globe,
    title: 'Региональный атлас России',
    description: 'Систематический обзор всех регионов страны в историко-градостроительном контексте.',
  },
];

export function Contents() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, sectionBg, textPrimary } = useThemeStyles();

  return (
    <section
      id="contents"
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
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Содержание</span>
          <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
            Что внутри Антологии
          </h2>
          <div className="gold-divider mx-auto" />
        </motion.div>

        {/* Contents Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {contents.map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`card-museum group relative transition-all duration-300 ${isDark ? 'bg-graphite-900/50 border-ivory-100/10 hover:border-gold-500/30' : 'bg-lightBgSecondary/70 border-lightBorder hover:border-gold-400/50'}`}
              >
                {/* Icon */}
                <div className="mb-6">
                  <div className={`w-14 h-14 border rounded-sm flex items-center justify-center transition-all duration-300 ${isDark ? 'border-gold-500/30 group-hover:border-gold-400 group-hover:bg-gold-500/10' : 'border-gold-400/40 group-hover:border-gold-600 group-hover:bg-gold-100/20'}`}>
                    <Icon className={`w-7 h-7 transition-colors ${isDark ? 'text-gold-400/80 group-hover:text-gold-400' : 'text-gold-600/80 group-hover:text-gold-700'}`} />
                  </div>
                </div>

                {/* Title */}
                <h3 className={`font-serif text-xl mb-3 transition-colors ${isDark ? 'text-ivory-50 group-hover:text-gold-400' : 'text-lightText group-hover:text-gold-600'}`}>
                  {item.title}
                </h3>

                {/* Description */}
                <p className={`text-sm leading-relaxed ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
                  {item.description}
                </p>

                {/* Decorative number */}
                <span className={`absolute top-6 right-6 font-serif text-4xl transition-colors ${isDark ? 'text-gold-500/10 group-hover:text-gold-500/20' : 'text-gold-400/10 group-hover:text-gold-400/20'}`}>
                  {String(index + 1).padStart(2, '0')}
                </span>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
