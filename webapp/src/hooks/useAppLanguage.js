import { useMemo, useState } from "react";
import { UI_TEXT } from "../constants/i18n";
import { getMiniAppLanguage, setMiniAppLanguage } from "../services/api";

export function useAppLanguage(initData) {
  const [language, setLanguage] = useState("en");
  const [languageLoading, setLanguageLoading] = useState(false);

  const t = useMemo(() => UI_TEXT[language] || UI_TEXT.en, [language]);

  const loadLanguage = async () => {
    if (!initData) return;
    try {
      setLanguageLoading(true);
      const data = await getMiniAppLanguage({ init_data: initData });
      if (data.language) setLanguage(data.language);
    } catch {
      setLanguage("en");
    } finally {
      setLanguageLoading(false);
    }
  };

  const updateLanguage = async (next) => {
    if (!initData) return;
    const data = await setMiniAppLanguage({
      init_data: initData,
      language: next
    });
    if (data.language) setLanguage(data.language);
  };

  return {
    language,
    languageLoading,
    t,
    loadLanguage,
    updateLanguage
  };
}
