import { motion, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { Check, AlertCircle, Send } from 'lucide-react';
import { useThemeStyles } from '../../hooks/useThemeStyles';

interface FormData {
  firstName: string;
  lastName: string;
  organization: string;
  position: string;
  email: string;
  phone: string;
  purpose: string;
  format: 'electronic' | 'paper' | 'both';
  consent: boolean;
}

interface FormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  purpose?: string;
  consent?: string;
}

const initialFormData: FormData = {
  firstName: '',
  lastName: '',
  organization: '',
  position: '',
  email: '',
  phone: '',
  purpose: '',
  format: 'electronic',
  consent: false,
};

export function RequestForm() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: '-100px' });
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'Укажите имя';
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Укажите фамилию';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Укажите email';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Некорректный формат email';
    }

    if (!formData.purpose.trim()) {
      newErrors.purpose = 'Укажите цель использования';
    }

    if (!formData.consent) {
      newErrors.consent = 'Необходимо согласие на обработку данных';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (validateForm()) {
      // TODO: connect to API endpoint /api/anthology/request-access
      console.log('Form submitted:', formData);
      setIsSubmitted(true);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const { isDark, textPrimary } = useThemeStyles();

  if (isSubmitted) {
    return (
      <section
        ref={containerRef}
        id="request-form"
        className={`section-padding ${isDark ? 'bg-graphite-900' : 'bg-lightBgSecondary'} relative transition-colors duration-500`}
      >
        <div className="section-container">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="max-w-2xl mx-auto text-center"
          >
            <div className={`w-20 h-20 mx-auto mb-8 border rounded-full flex items-center justify-center ${isDark ? 'border-gold-500 bg-graphite-950' : 'border-gold-600 bg-lightBg'}`}>
              <Check className={`w-10 h-10 ${isDark ? 'text-gold-400' : 'text-gold-600'}`} />
            </div>
            <h3 className={`font-serif text-3xl ${textPrimary} mb-4`}>
              Заявка принята
            </h3>
            <p className={`text-lg mb-8 ${isDark ? 'text-ivory-300/80' : 'text-lightTextSecondary/80'}`}>
              После рассмотрения мы свяжемся с вами и направим информацию о доступе.
            </p>
            <button
              onClick={() => {
                setIsSubmitted(false);
                setFormData(initialFormData);
              }}
              className="btn-secondary"
            >
              Отправить ещё одну заявку
            </button>
          </motion.div>
        </div>
      </section>
    );
  }

  return (
    <section
      ref={containerRef}
      id="request-form"
      className={`section-padding ${isDark ? 'bg-graphite-900' : 'bg-lightBgSecondary'} relative transition-colors duration-500`}
    >
      {/* Decorative frame */}
      <div className={`absolute inset-0 border-8 pointer-events-none ${isDark ? 'border-graphite-950' : 'border-lightBg'}`} />

      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto"
        >
          {/* Section Header */}
          <div className="text-center mb-12">
            <span className={`museum-label block mb-4 ${isDark ? 'text-ivory-400/70' : 'text-gold-800'}`}>Заявка на доступ</span>
            <h2 className={`font-serif text-3xl sm:text-4xl md:text-5xl ${textPrimary} mb-6`}>
              Запросить доступ к Антологии
            </h2>
            <p className={isDark ? 'text-ivory-300/70' : 'text-lightTextSecondary/70'}>
              Заполните форму, и мы свяжемся с вами для предоставления доступа
            </p>
            <div className="gold-divider mx-auto mt-6" />
          </div>

          {/* Form */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            {/* Two columns - Name */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Имя <span className={isDark ? 'text-gold-400' : 'text-gold-700'}>*</span>
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className={`input-field ${errors.firstName ? 'border-burgundy-500' : ''}`}
                  placeholder="Иван"
                />
                {errors.firstName && (
                  <p className="mt-1 text-sm text-burgundy-400 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.firstName}
                  </p>
                )}
              </div>

              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Фамилия <span className={isDark ? 'text-gold-400' : 'text-gold-700'}>*</span>
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className={`input-field ${errors.lastName ? 'border-burgundy-500' : ''}`}
                  placeholder="Иванов"
                />
                {errors.lastName && (
                  <p className="mt-1 text-sm text-burgundy-400 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.lastName}
                  </p>
                )}
              </div>
            </div>

            {/* Organization & Position */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Организация / проект
                </label>
                <input
                  type="text"
                  name="organization"
                  value={formData.organization}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Название организации"
                />
              </div>

              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Должность
                </label>
                <input
                  type="text"
                  name="position"
                  value={formData.position}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="Архитектор, исследователь..."
                />
              </div>
            </div>

            {/* Email & Phone */}
            <div className="grid sm:grid-cols-2 gap-6">
              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Email <span className={isDark ? 'text-gold-400' : 'text-gold-700'}>*</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={`input-field ${errors.email ? 'border-burgundy-500' : ''}`}
                  placeholder="email@example.com"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-burgundy-400 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.email}
                  </p>
                )}
              </div>

              <div>
                <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                  Телефон
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="input-field"
                  placeholder="+7 (___) ___-__-__"
                />
              </div>
            </div>

            {/* Purpose */}
            <div>
              <label className={`block text-sm mb-2 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                Цель использования <span className={isDark ? 'text-gold-400' : 'text-gold-700'}>*</span>
              </label>
              <textarea
                name="purpose"
                value={formData.purpose}
                onChange={handleChange}
                rows={3}
                className={`input-field resize-none ${
                  errors.purpose ? 'border-burgundy-500' : ''
                }`}
                placeholder="Опишите, для каких целей вам нужна Антология..."
              />
              {errors.purpose && (
                <p className="mt-1 text-sm text-burgundy-400 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.purpose}
                </p>
              )}
            </div>

            {/* Format selection */}
            <div>
              <label className={`block text-sm mb-4 ${isDark ? 'text-ivory-300' : 'text-lightText'}`}>
                Интересующий формат
              </label>
              <div className="grid sm:grid-cols-3 gap-4">
                {[
                  { value: 'electronic', label: 'Электронная версия' },
                  { value: 'paper', label: 'Бумажный комплект' },
                  { value: 'both', label: 'Оба варианта' },
                ].map((option) => (
                  <label
                    key={option.value}
                    className={`relative cursor-pointer border rounded-sm p-4 text-center transition-all duration-300 ${
                      formData.format === option.value
                        ? isDark
                          ? 'border-gold-500 bg-gold-500/10'
                          : 'border-gold-700 bg-gold-700/10'
                        : isDark
                        ? 'border-ivory-100/20 hover:border-ivory-100/40'
                        : 'border-gold-700/30 hover:border-gold-700/60'
                    }`}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={option.value}
                      checked={formData.format === option.value}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <span
                      className={`text-sm font-medium ${
                        formData.format === option.value
                          ? isDark ? 'text-gold-400' : 'text-gold-800'
                          : isDark ? 'text-ivory-300' : 'text-lightText'
                      }`}
                    >
                      {option.label}
                    </span>
                    {formData.format === option.value && (
                      <div className={`absolute top-2 right-2 w-2 h-2 rounded-full ${isDark ? 'bg-gold-500' : 'bg-gold-700'}`} />
                    )}
                  </label>
                ))}
              </div>
            </div>

            {/* Consent */}
            <div>
              <label className="flex items-start gap-3 cursor-pointer group">
                <div className="relative mt-1">
                  <input
                    type="checkbox"
                    name="consent"
                    checked={formData.consent}
                    onChange={handleChange}
                    className="sr-only"
                  />
                  <div
                    className={`w-5 h-5 border rounded-sm transition-all duration-200 ${
                      formData.consent
                        ? isDark ? 'border-gold-500 bg-gold-500' : 'border-gold-700 bg-gold-700'
                        : errors.consent
                        ? 'border-burgundy-500'
                        : isDark
                        ? 'border-ivory-100/40 group-hover:border-ivory-100/60'
                        : 'border-gold-700/50 group-hover:border-gold-700'
                    }`}
                  >
                    {formData.consent && (
                      <Check className={`w-4 h-4 absolute top-0.5 left-0.5 ${isDark ? 'text-graphite-950' : 'text-white'}`} />
                    )}
                  </div>
                </div>
                <span className={`text-sm leading-relaxed ${isDark ? 'text-ivory-300/80' : 'text-lightText/80'}`}>
                  Я даю согласие на обработку персональных данных и подтверждаю, что
                  ознакомился с{' '}
                  <a href="#" className={`underline ${isDark ? 'text-gold-400 hover:text-gold-300' : 'text-gold-700 hover:text-gold-600'}`}>
                    политикой обработки персональных данных
                  </a>
                </span>
              </label>
              {errors.consent && (
                <p className="mt-2 text-sm text-burgundy-400 flex items-center gap-1 ml-8">
                  <AlertCircle className="w-4 h-4" />
                  {errors.consent}
                </p>
              )}
            </div>

            {/* Submit */}
            <div className="pt-4">
              <button type="submit" className="btn-primary w-full sm:w-auto group">
                <Send className="w-5 h-5 mr-2 group-hover:translate-x-1 transition-transform" />
                Отправить заявку
              </button>
            </div>
          </motion.form>
        </motion.div>
      </div>
    </section>
  );
}
