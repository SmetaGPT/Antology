import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const navItems = [
  { label: 'О проекте', href: '#about' },
  { label: 'Содержание', href: '#contents' },
  { label: 'Тома', href: '#volumes' },
  { label: 'Для кого', href: '#audience' },
  { label: 'Доступ', href: '#access' },
  { label: 'FAQ', href: '#faq' },
];

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        isScrolled
          ? theme === 'dark'
            ? 'bg-graphite-950/90 border-b border-ivory-100/10'
            : 'bg-lightBgSecondary/95 border-b border-lightBorder'
          : theme === 'dark'
          ? 'bg-transparent'
          : 'bg-transparent'
      } backdrop-blur-md`}
    >
      <div className="section-container">
        <nav className="flex items-center justify-between h-20">
          {/* Logo */}
          <a href="#top" className="flex items-center gap-3 group">
            <div
              className={`w-10 h-10 border rounded-sm flex items-center justify-center transition-colors ${
                theme === 'dark'
                  ? 'border-gold-500/40 group-hover:border-gold-400'
                  : 'border-lightAccent/40 group-hover:border-lightAccent'
              }`}
            >
              <span
                className={`font-serif text-lg font-bold ${
                  theme === 'dark' ? 'text-gold-400' : 'text-lightAccent'
                }`}
              >
                А
              </span>
            </div>
            <span
              className={`font-serif text-xl hidden sm:block transition-colors ${
                theme === 'dark'
                  ? 'text-ivory-100 group-hover:text-gold-400'
                  : 'text-lightText group-hover:text-lightAccent'
              }`}
            >
              Антология
            </span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`text-sm font-medium tracking-wide transition-colors relative group ${
                  theme === 'dark'
                    ? 'text-ivory-300 hover:text-gold-400'
                    : 'text-lightTextSecondary hover:text-lightAccent'
                }`}
              >
                {item.label}
                <span
                  className={`absolute -bottom-1 left-0 w-0 h-px transition-all duration-300 group-hover:w-full ${
                    theme === 'dark' ? 'bg-gold-400' : 'bg-lightAccent'
                  }`}
                />
              </a>
            ))}
          </div>

          {/* Theme Toggle & CTA */}
          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-sm transition-all duration-300 ${
                theme === 'dark'
                  ? 'text-ivory-300 hover:text-gold-400 hover:bg-ivory-100/5'
                  : 'text-lightTextSecondary hover:text-lightAccent hover:bg-lightAccent/5'
              }`}
              aria-label="Переключить тему"
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>

            <div className="hidden lg:block">
              <a
                href="#request-form"
                className={`btn-ghost border rounded-sm ${
                  theme === 'dark'
                    ? 'border-gold-500/30 hover:border-gold-400'
                    : 'border-lightAccent/30 hover:border-lightAccent'
                }`}
              >
                Запросить доступ
              </a>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className={`lg:hidden p-2 transition-colors ${
                theme === 'dark'
                  ? 'text-ivory-100 hover:text-gold-400'
                  : 'text-lightText hover:text-lightAccent'
              }`}
              aria-label="Меню"
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </nav>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className={`lg:hidden border-t ${
              theme === 'dark'
                ? 'bg-graphite-950/95 border-ivory-100/10'
                : 'bg-lightBgSecondary/95 border-lightBorder'
            } backdrop-blur-md`}
          >
            <div className="section-container py-6">
              <div className="flex flex-col gap-4">
                {navItems.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`text-base font-medium py-2 transition-colors ${
                      theme === 'dark'
                        ? 'text-ivory-300 hover:text-gold-400'
                        : 'text-lightText hover:text-lightAccent'
                    }`}
                  >
                    {item.label}
                  </a>
                ))}
                <a
                  href="#request-form"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="btn-primary mt-2"
                >
                  Запросить доступ
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
