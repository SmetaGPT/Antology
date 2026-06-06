import { motion, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const faqs = [
  {
    question: 'Как получить электронную версию?',
    answer:
      'Для получения электронной версии необходимо заполнить заявку на нашем сайте. После рассмотрения заявки и регистрации вы получите доступ к электронной версии Антологии.',
  },
  {
    question: 'Нужно ли регистрироваться?',
    answer:
      'Да, доступ к Антологии предоставляется зарегистрированным пользователям. После отправки заявки мы направим вам инструкции по регистрации и доступу.',
  },
  {
    question: 'Можно ли получить бумажный комплект?',
    answer:
      'Бумажный комплект Антологии передаётся по отдельным запросам. Заполните форму заявки и укажите ваш интерес в соответствующем поле.',
  },
  {
    question: 'Кому подойдёт Антология?',
    answer:
      'Антология будет полезна архитекторам, градостроителям, проектировщикам, преподавателям, студентам, краеведам, музейным работникам, специалистам туристиpческой сферы и всем, кто интересуется историей России.',
  },
  {
    question: 'Можно ли использовать материалы в образовательных и культурных проектах?',
    answer:
      'Да, материалы Антологии могут использоваться в образовательных, научных и культурных проектах. Укажите цель использования при заполнении заявки.',
  },
  {
    question: 'Когда я получу ответ по заявке?',
    answer:
      'Рассмотрение заявок занимает обычно от нескольких дней до двух недель. Мы свяжемся с вами по указанному email или телефону.',
  },
];

export function FAQ() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const { isDark, sectionBg, textPrimary } = useThemeStyles();

  const toggleFaq = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section
      id="faq"
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
          <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Вопросы и ответы</span>
          <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
            Часто задаваемые вопросы
          </h2>
          <div className="gold-divider mx-auto" />
        </motion.div>

        {/* FAQ List */}
        <div className="max-w-3xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.08 }}
              className={`border rounded-sm overflow-hidden transition-colors ${isDark ? 'border-ivory-100/10 hover:border-gold-500/30' : 'border-lightBorder hover:border-gold-400/50'}`}
            >
              <button
                onClick={() => toggleFaq(index)}
                className={`w-full flex items-center justify-between p-6 text-left group transition-colors ${isDark ? 'hover:bg-graphite-900/30' : 'hover:bg-lightBgSecondary/50'}`}
              >
                <h3 className={`font-serif text-lg pr-4 transition-colors ${isDark ? 'text-ivory-100 group-hover:text-gold-400' : 'text-lightText group-hover:text-gold-600'}`}>
                  {faq.question}
                </h3>
                <motion.div
                  animate={{ rotate: openIndex === index ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex-shrink-0"
                >
                  <ChevronDown className={`w-5 h-5 transition-colors ${isDark ? 'text-gold-400/60 group-hover:text-gold-400' : 'text-gold-600/60 group-hover:text-gold-700'}`} />
                </motion.div>
              </button>

              <motion.div
                initial={false}
                animate={{
                  height: openIndex === index ? 'auto' : 0,
                  opacity: openIndex === index ? 1 : 0,
                }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-6">
                  <div className="gold-line mb-4" />
                  <p className={`leading-relaxed ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
                    {faq.answer}
                  </p>
                </div>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
