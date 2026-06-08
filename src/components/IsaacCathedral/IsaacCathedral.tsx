import { AnimatePresence, motion, useInView } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import { Users, Award, BookOpen, Expand, X } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';
import { assetUrl } from '../../utils/assetUrl';

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

const galleryImages = [
  {
    src: assetUrl('/isaac-gallery/01-cathedral.jpeg'),
    alt: 'Исаакиевский собор в Санкт-Петербурге вечером',
    caption: 'Исаакиевский собор',
  },
  {
    src: assetUrl('/isaac-gallery/02-photo1.jpg'),
    alt: 'Гости презентации в интерьере Исаакиевского собора',
    caption: 'Зал презентации',
  },
  {
    src: assetUrl('/isaac-gallery/03-photo2.jpg'),
    alt: 'Участники официальной презентации издания',
    caption: 'Официальная презентация',
  },
  {
    src: assetUrl('/isaac-gallery/04-photo3.jpg'),
    alt: 'Момент мероприятия в Исаакиевском соборе',
    caption: 'Профессиональное сообщество',
  },
  {
    src: assetUrl('/isaac-gallery/05-photo4.jpg'),
    alt: 'Передача издания во время презентации',
    caption: 'Передача книжного комплекта',
  },
];

export function IsaacCathedral() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const { isDark, textPrimary, accentGold } = useThemeStyles();
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);

  useEffect(() => {
    if (!isHovered || galleryImages.length < 2) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setActiveImageIndex((currentIndex) => (currentIndex + 1) % galleryImages.length);
    }, 2000);

    return () => window.clearTimeout(timeoutId);
  }, [activeImageIndex, isHovered]);

  useEffect(() => {
    if (!isLightboxOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsLightboxOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isLightboxOpen]);

  const activeImage = galleryImages[activeImageIndex];

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
          className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center lg:items-start"
        >
          {/* Image */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative lg:w-[105%] lg:pt-14"
          >
            <div className="relative">
              {/* Decorative frame */}
              <div className={`absolute -inset-4 border rounded-sm ${isDark ? 'border-gold-500/30' : 'border-gold-400/40'}`} />

              <button
                type="button"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
                onFocus={() => setIsHovered(true)}
                onBlur={() => setIsHovered(false)}
                onClick={() => setIsLightboxOpen(true)}
                className={`group relative block w-full overflow-hidden rounded-sm border text-left transition-all duration-300 ${
                  isDark
                    ? 'border-ivory-100/10 bg-graphite-950/80 hover:border-gold-500/40'
                    : 'border-lightBorder bg-lightBg hover:border-gold-400/50'
                }`}
                aria-label={`Открыть фотографию: ${activeImage.alt}`}
              >
                <div className="relative aspect-[4/3] sm:aspect-[16/10]">
                  <AnimatePresence mode="wait">
                    <motion.img
                      key={activeImage.src}
                      src={activeImage.src}
                      alt={activeImage.alt}
                      initial={{ opacity: 0.2, scale: 1.03 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0.2, scale: 0.985 }}
                      transition={{ duration: 0.45, ease: 'easeOut' }}
                      className="absolute inset-0 h-full w-full object-cover object-center"
                    />
                  </AnimatePresence>

                  <div className={`absolute inset-0 bg-gradient-to-t ${isDark ? 'from-graphite-950 via-graphite-950/8 to-transparent' : 'from-black/55 via-black/10 to-transparent'}`} />

                  <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-4 p-5 sm:p-6">
                    <div>
                      <div className={`mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] ${isDark ? 'text-gold-400/80' : 'text-gold-200'}`}>
                        Фотоархив презентации
                      </div>
                      <div className={`font-serif text-xl sm:text-2xl leading-none ${isDark ? 'text-ivory-100' : 'text-white'}`}>
                        {activeImage.caption}
                      </div>
                    </div>

                    <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-sm border transition-all duration-300 ${
                      isDark
                        ? 'border-ivory-100/15 bg-graphite-900/75 text-gold-300 group-hover:border-gold-500/40'
                        : 'border-lightBorder bg-white/85 text-gold-700 group-hover:border-gold-400/50'
                    }`}>
                      <Expand className="h-5 w-5" />
                    </div>
                  </div>

                  <div className="absolute left-5 top-5 flex gap-2 sm:left-6 sm:top-6">
                    {galleryImages.map((image, index) => (
                      <span
                        key={image.src}
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          index === activeImageIndex
                            ? isDark
                              ? 'w-7 bg-gold-400'
                              : 'w-7 bg-gold-600'
                            : isDark
                              ? 'w-3 bg-ivory-100/25'
                              : 'w-3 bg-lightText/20'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </button>

              {/* Overlay gradient */}
              <div className="pointer-events-none absolute inset-x-0 -bottom-10 flex justify-center">
                <div className={`rounded-full border px-4 py-2 text-[11px] font-medium uppercase tracking-[0.16em] ${
                  isDark
                    ? 'border-gold-500/20 bg-graphite-950/85 text-ivory-300/80'
                    : 'border-gold-400/30 bg-white/90 text-lightTextSecondary'
                }`}>
                  Наведите, чтобы начать просмотр. Нажмите, чтобы увеличить.
                </div>
              </div>
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

      <AnimatePresence>
        {isLightboxOpen ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/82 px-4 py-6 backdrop-blur-sm"
            onClick={() => setIsLightboxOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: 12 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="relative w-full max-w-6xl"
              onClick={(event) => event.stopPropagation()}
            >
              <button
                type="button"
                onClick={() => setIsLightboxOpen(false)}
                className="absolute right-3 top-3 z-10 flex h-11 w-11 items-center justify-center rounded-sm border border-white/15 bg-black/45 text-white transition-colors hover:border-gold-400/50 hover:text-gold-300"
                aria-label="Закрыть увеличенное фото"
              >
                <X className="h-5 w-5" />
              </button>

              <div className="overflow-hidden rounded-sm border border-white/10 bg-black/40 shadow-2xl">
                <img
                  src={activeImage.src}
                  alt={activeImage.alt}
                  className="max-h-[82vh] w-full object-contain"
                />
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}
