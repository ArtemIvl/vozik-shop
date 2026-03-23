import { useEffect, useState } from "react";
import LoadingPulse from "../components/common/LoadingPulse";
import { getMiniAppGiftPromo } from "../services/api";

export default function GiftPromoPage({ initData, t }) {
  const [captionHtml, setCaptionHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadPromo = async () => {
      if (!initData) return;
      try {
        setLoading(true);
        setError("");
        const response = await getMiniAppGiftPromo({ init_data: initData });
        setCaptionHtml(response.captionHtml || "");
      } catch (requestError) {
        setError(requestError.message || t.claimGift);
      } finally {
        setLoading(false);
      }
    };

    loadPromo();
  }, [initData]);

  return (
    <section className="space-y-4">
      <p className="text-xs uppercase tracking-[0.14em] text-tg-muted">{t.claimGift}</p>

      <div className="overflow-hidden rounded-3xl border border-white/10 bg-tg-surface">
        <img src="/gift-bear.jpeg" alt="Gift promo" className="h-56 w-full object-cover" />
        <div className="p-4">
          {loading ? <LoadingPulse label={t.loading} /> : null}
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          {!loading && !error ? (
            <div
              className="gift-html text-sm text-tg-text"
              dangerouslySetInnerHTML={{ __html: captionHtml }}
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}
