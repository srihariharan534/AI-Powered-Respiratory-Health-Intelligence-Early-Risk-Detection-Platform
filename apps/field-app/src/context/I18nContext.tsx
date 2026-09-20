import React, { createContext, useContext, useState } from 'react';
import en from '../i18n/en.json';
import ta from '../i18n/ta.json';

type Locale = 'en' | 'ta';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const dictionaries: Record<Locale, Record<string, string>> = { en, ta };

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocale] = useState<Locale>('en');

  const t = (key: string): string => {
    return dictionaries[locale][key] || dictionaries['en'][key] || key;
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};
