import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ArrowRight } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const volumes = [
  {
    number: 'I–II',
    title: 'Наследие',
    subtitle: 'Цивилизационный код',
    description: 'Фундаментальные основы российского градостроительства и исторического расселения.',
  },
  {
    number: 'III',
    title: 'Истоки',
    subtitle: 'У истоков российского градостроительства',
    description: 'Древнейшие города и первые градостроительные традиции.',
  },
  {
    number: 'IV',
    title: 'Центр',
    subtitle: 'Центральный федеральный округ',
    description: 'Исторические города и сёла центральной России.',
  },
  {
    number: 'V',
    title: 'Северо-Запад',
    subtitle: 'Северо-Западный федеральный округ',
    description: 'Санкт-Петербург, Новгород, Псков и другие.',
  },
  {
    number: 'VI',
    title: 'Поволжье',
    subtitle: 'Приволжский федеральный округ',
    description: 'Города и сёла вдоль Волги и Камы.',
  },
  {
    number: 'VII',
    title: 'Юг и Кавказ',
    subtitle: 'Южный и Северо-Кавказский ФО',
    description: 'Кубань, Дон, Ставрополье, Кавказ.',
  },
  {
    number: 'VIII',
    title: 'Урал',
    subtitle: 'Уральский федеральный округ',
    description: 'Уральские города промышленного наследия.',
  },
  {
    number: 'IX',
    title: 'Сибирь',
    subtitle: 'Сибирский федеральный округ',
    description: 'Города Сибири от Енисея до Байкала.',
  },
  {
    number: 'X',
    title: 'Дальний Восток',
    subtitle: 'Дальневосточный федеральный округ',
    description: 'Города и сёла восточных рубежей России.',
  },
  {
    number: 'XI',
    title: 'Крым',
    subtitle: 'Крым и Новороссия',
    description: 'Исторические населённые пункты Крыма и Северного Причерноморья.',
  },
  {
    number: 'XII',
    title: 'Москва и Казань',
    subtitle: 'Москва и Казань',
    description: ' специальные разделы о двух столицах.',
  },
  {
    number: 'XIII',
    title: 'Петербург',
    subtitle: 'Санкт-Петербург и Севастополь',
    description: 'Два города федерального значения.',
  },
];

export function Volumes() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, textPrimary } = useThemeStyles();

  return (
    <section
      id="volumes"
      ref={containerRef}
      className={`section-padding ${isDark ? 'bg-gradient-to-b from-graphite-950 via-graphite-900/30 to-graphite-950' : 'bg-gradient-to-b from-lightBg via-lightBgSecondary/20 to-lightBg'} relative overflow-hidden transition-colors duration-500`}
    >
      {/* Decorative line */}
      <div className={`absolute top-0 left-0 w-full gold-line ${isDark ? 'from-gold-600/0 via-gold-500/50 to-gold-600/0' : 'from-gold-500/0 via-gold-400/30 to-gold-500/0'}`} />

      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Путешествие</span>
          <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
            Путешествие по томам
          </h2>
          <p className={`max-w-2xl mx-auto ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
            Маршрут по исторической карте России — от цивилизационных истоков до
            дальневосточных рубежей
          </p>
          <div className="gold-divider mx-auto mt-6" />
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Connecting line */}
          <div className={`absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b hidden lg:block ${isDark ? 'from-gold-500/50 via-gold-500/30 to-transparent' : 'from-gold-400/40 via-gold-400/20 to-transparent'}`} />

          {/* Volumes Grid */}
          <div className="grid lg:grid-cols-2 gap-6 lg:gap-12">
            {volumes.map((volume, index) => (
              <motion.div
                key={volume.number}
                initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
                animate={isInView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.08 }}
                className={`relative ${index % 2 === 0 ? 'lg:pr-8' : 'lg:pl-8'}`}
              >
                {/* Timeline dot - visible on lg screens */}
                <div
                  className={`absolute top-8 ${
                    index % 2 === 0 ? '-right-4' : '-left-4'
                  } w-2 h-2 rounded-full hidden lg:block transition-colors ${isDark ? 'bg-gold-500' : 'bg-gold-600'}`}
                />

                <div className={`card-museum relative group overflow-hidden transition-all duration-300 ${isDark ? 'bg-graphite-900/50 border-ivory-100/10 hover:border-gold-500/30 hover:shadow-museum' : 'bg-lightBgSecondary/70 border-lightBorder hover:border-gold-400/50 hover:shadow-light-shadow'}`}>
                  {/* Volume number badge */}
                  <div className={`absolute top-0 right-0 px-4 py-2 text-xs font-bold tracking-wider rounded-bl-sm transition-colors ${isDark ? 'bg-gradient-to-bl from-gold-600 to-gold-700 text-graphite-950' : 'bg-gradient-to-bl from-gold-600 to-gold-700 text-white'}`}>
                    Т. {volume.number}
                  </div>

                  <div className="pt-8 pr-16">
                    <h3 className={`font-serif text-xl transition-colors mb-1 ${isDark ? 'text-ivory-50 group-hover:text-gold-400' : 'text-lightText group-hover:text-gold-600'}`}>
                      {volume.title}
                    </h3>
                    <p className={`text-sm tracking-wide mb-3 transition-colors ${isDark ? 'text-gold-400/80' : 'text-gold-600/80'}`}>
                      {volume.subtitle}
                    </p>
                    <p className={`text-sm leading-relaxed transition-colors ${isDark ? 'text-ivory-300/60' : 'text-lightTextSecondary'}`}>
                      {volume.description}
                    </p>
                  </div>

                  {/* Arrow indicator */}
                  <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ArrowRight className={`w-5 h-5 ${isDark ? 'text-gold-400' : 'text-gold-600'}`} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
