import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';

interface ImagePlaceholderProps {
  src?: string;
  alt: string;
  className?: string;
  aspectRatio?: 'video' | 'square' | 'portrait' | 'wide' | 'auto';
  overlay?: boolean;
  overlayText?: string;
}

const aspectRatios = {
  video: 'aspect-video',
  square: 'aspect-square',
  portrait: 'aspect-[3/4]',
  wide: 'aspect-[21/9]',
  auto: 'aspect-auto',
};

export function ImagePlaceholder({
  src,
  alt,
  className = '',
  aspectRatio = 'video',
  overlay = false,
  overlayText,
}: ImagePlaceholderProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const imageExists = false;

  if (!imageExists || !src) {
    return (
      <div
        className={`image-placeholder ${aspectRatios[aspectRatio]} ${className} relative overflow-hidden`}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
          <motion.div
            initial={{ opacity: 0.3 }}
            animate={{ opacity: [0.3, 0.5, 0.3] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            className={`w-16 h-16 border rounded-sm flex items-center justify-center mb-3 ${isDark ? 'border-gold-500/30' : 'border-gold-600/30'}`}
          >
            <div className={`w-8 h-8 border rounded-full ${isDark ? 'border-gold-400/40' : 'border-gold-600/40'}`} />
          </motion.div>
          <p className={`text-sm font-light tracking-wide ${isDark ? 'text-ivory-400/60' : 'text-lightTextSecondary/70'}`}>
            {overlayText || alt}
          </p>
        </div>
        <div className={`absolute inset-0 bg-gradient-to-t ${isDark ? 'from-graphite-950/80 via-transparent to-transparent' : 'from-lightBg/40 via-transparent to-transparent'}`} />
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden ${className}`}>
      <img src={src} alt={alt} className="w-full h-full object-cover" />
      {overlay && (
        <div className="absolute inset-0 bg-graphite-950/40" />
      )}
    </div>
  );
}
