import { motion } from 'framer-motion';
import { useThemeStyles } from '../../hooks/useThemeStyles';

const navLinks = [
  { label: 'О проекте', href: '#about' },
  { label: 'Содержание', href: '#contents' },
  { label: 'Тома', href: '#volumes' },
  { label: 'Для кого', href: '#audience' },
  { label: 'Доступ', href: '#access' },
  { label: 'FAQ', href: '#faq' },
];

const legalLinks = [
  { label: 'Политика обработки персональных данных', href: '/privacy-policy.html' },
  { label: 'Пользовательское соглашение', href: '/terms.html' },
];

export function Footer() {
  const { isDark } = useThemeStyles();

  return (
    <footer className={`${isDark ? 'bg-graphite-950 border-ivory-100/10' : 'bg-lightBgSecondary border-lightBorder'} border-t relative transition-colors duration-500`}>
      <div className="section-container py-16 md:py-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-12">
          {/* Logo & Description */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="lg:col-span-2"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 border rounded-sm flex items-center justify-center transition-colors ${isDark ? 'border-gold-500/40' : 'border-gold-400/40'}`}>
                <span className={`font-serif text-lg font-bold ${isDark ? 'text-gold-400' : 'text-gold-600'}`}>А</span>
              </div>
              <span className={`font-serif text-xl transition-colors ${isDark ? 'text-ivory-100' : 'text-lightText'}`}>Антология</span>
            </div>
            <p className={`text-sm leading-relaxed mb-4 max-w-md transition-colors ${isDark ? 'text-ivory-300/60' : 'text-lightTextSecondary'}`}>
              Антология «Исторические города и сёла России» — цифровой атлас градостроительной
              памяти России. 10 томов, 13 книг, более 6200 исторических населённых пунктов.
            </p>
            <p className={`text-xs transition-colors ${isDark ? 'text-ivory-400/50' : 'text-lightTextSecondary/70'}`}>
              Издание представлено в Государственном музее «Исаакиевский собор»
            </p>
          </motion.div>

          {/* Navigation */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            viewport={{ once: true }}
          >
            <h4 className={`font-serif text-base mb-4 transition-colors ${isDark ? 'text-ivory-100' : 'text-lightText'}`}>Навигация</h4>
            <ul className="space-y-2">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className={`text-sm transition-colors ${isDark ? 'text-ivory-300/70 hover:text-gold-400' : 'text-lightTextSecondary hover:text-gold-600'}`}
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Contacts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
          >
            <h4 className={`font-serif text-base mb-4 transition-colors ${isDark ? 'text-ivory-100' : 'text-lightText'}`}>Контакты</h4>
            <ul className="space-y-3">
              <li className={`text-sm transition-colors ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
                <span className={`block text-xs mb-1 transition-colors ${isDark ? 'text-ivory-400/50' : 'text-lightTextSecondary/70'}`}>Основной канал</span>
                <a href="#request-form" className={`transition-colors ${isDark ? 'hover:text-gold-400' : 'hover:text-gold-600'}`}>
                  Форма запроса на сайте
                </a>
              </li>
              <li className={`text-sm transition-colors ${isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary'}`}>
                <span className={`block text-xs mb-1 transition-colors ${isDark ? 'text-ivory-400/50' : 'text-lightTextSecondary/70'}`}>Режим обработки</span>
                <span>Электронные заявки обрабатываются автоматически, запросы на печатный комплект проходят ручное рассмотрение.</span>
              </li>
            </ul>
          </motion.div>
        </div>

        {/* Bottom bar */}
        <div className={`mt-12 pt-8 border-t transition-colors ${isDark ? 'border-ivory-100/10' : 'border-lightBorder'}`}>
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="flex flex-wrap justify-center md:justify-start gap-4 md:gap-6"
            >
              {legalLinks.map((link, index) => (
                <a
                  key={link.href + index}
                  href={link.href}
                  className={`text-xs transition-colors ${isDark ? 'text-ivory-400/50 hover:text-gold-400' : 'text-lightTextSecondary/70 hover:text-gold-600'}`}
                >
                  {link.label}
                </a>
              ))}
            </motion.div>

            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
              className={`text-xs transition-colors ${isDark ? 'text-ivory-400/40' : 'text-lightTextSecondary/60'}`}
            >
              © {new Date().getFullYear()} Антология «Исторические города и сёла России»
            </motion.p>
          </div>
        </div>
      </div>

      {/* Decorative top line */}
      <div className="absolute top-0 left-0 w-full gold-line" />
    </footer>
  );
}
