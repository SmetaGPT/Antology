import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { FileText, Target, CheckCircle, BookOpen } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const steps = [
  {
    icon: FileText,
    number: '01',
    title: 'Заполните заявку',
    description: 'Укажите ваши данные и интересующий формат доступа к изданию.',
  },
  {
    icon: Target,
    number: '02',
    title: 'Укажите цель использования',
    description: 'Сообщите, для каких целей вам необходимо издание — это поможет нам быстрее рассмотреть заявку.',
  },
  {
    icon: CheckCircle,
    number: '03',
    title: 'Получите электронный доступ',
    description: 'После рассмотрения заявки и регистрации вы получите доступ к электронной версии.',
  },
  {
    icon: BookOpen,
    number: '04',
    title: 'Бумажный комплект',
    description: 'При необходимости подайте отдельный запрос на бумажный комплект.',
  },
];

export function AccessSteps() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, textPrimary } = useThemeStyles();

  return (
    <section
      id="access"
      ref={containerRef}
      className={`section-padding ${isDark ? 'bg-gradient-to-b from-graphite-950 via-graphite-900/30 to-graphite-950' : 'bg-gradient-to-b from-lightBg via-lightBgSecondary/20 to-lightBg'} relative transition-colors duration-500`}
    >
      {/* Decorative lines */}
      <div className={`absolute top-0 left-0 w-full gold-line ${isDark ? 'from-gold-600/0 via-gold-500/50 to-gold-600/0' : 'from-gold-500/0 via-gold-400/30 to-gold-500/0'}`} />

      <div className="section-container">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Порядок доступа</span>
          <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
            Как получить доступ
          </h2>
          <p className={`max-w-2xl mx-auto ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
            Доступ к Антологии предоставляется зарегистрированным пользователям после рассмотрения заявки
          </p>
          <div className="gold-divider mx-auto mt-6" />
        </motion.div>

        {/* Steps */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="relative group"
              >
                {/* Step card */}
                <div className={`card-museum text-center h-full flex flex-col transition-all duration-300 ${isDark ? 'bg-graphite-900/50 border-ivory-100/10 hover:border-gold-500/30' : 'bg-lightBgSecondary/70 border-lightBorder hover:border-gold-400/50'}`}>
                  {/* Number badge */}
                  <div className={`absolute -top-3 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 ${isDark ? 'bg-gold-500 text-graphite-950' : 'bg-gold-600 text-white'}`}>
                    {index + 1}
                  </div>

                  {/* Content */}
                  <div className="pt-6 flex-1 flex flex-col">
                    <div className={`w-16 h-16 mx-auto mb-4 border rounded-sm flex items-center justify-center transition-all duration-300 ${isDark ? 'border-gold-500/30 group-hover:border-gold-400 group-hover:bg-gold-500/10' : 'border-gold-400/40 group-hover:border-gold-600 group-hover:bg-gold-100/20'}`}>
                      <Icon className={`w-8 h-8 transition-colors ${isDark ? 'text-gold-400/80 group-hover:text-gold-400' : 'text-gold-600/80 group-hover:text-gold-700'}`} />
                    </div>

                    <h3 className={`font-serif text-lg mb-2 transition-colors ${isDark ? 'text-ivory-50 group-hover:text-gold-400' : 'text-lightText group-hover:text-gold-600'}`}>
                      {step.title}
                    </h3>

                    <p className={`text-sm leading-relaxed flex-1 ${isDark ? 'text-ivory-300/60' : 'text-lightTextSecondary'}`}>
                      {step.description}
                    </p>
                  </div>
                </div>

                {/* Connecting arrow - visible between steps on large screens */}
                {index < steps.length - 1 && (
                  <div className={`hidden lg:block absolute top-1/2 -right-4 w-8 h-px bg-gradient-to-r transform -translate-y-1/2 ${isDark ? 'from-gold-500/50 to-transparent' : 'from-gold-400/40 to-transparent'}`} />
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
