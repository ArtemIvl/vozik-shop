import { useEffect, useRef } from "react";

export default function AppShell({ children, bottomNav = null, scrollKey = "" }) {
  const shellRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    const shell = shellRef.current;
    if (!shell) return undefined;

    const syncAppHeight = () => {
      shell.style.setProperty("--app-height", `${window.innerHeight}px`);
    };

    syncAppHeight();
    window.addEventListener("orientationchange", syncAppHeight);

    return () => {
      window.removeEventListener("orientationchange", syncAppHeight);
      shell.style.removeProperty("--app-height");
    };
  }, []);

  useEffect(() => {
    const content = contentRef.current;
    if (!content) return;
    content.scrollTo({ top: 0, behavior: "auto" });
  }, [scrollKey]);

  return (
    <main
      ref={shellRef}
      className="relative mx-auto w-full max-w-md text-tg-text"
      style={{ height: "var(--app-height, 100vh)" }}
    >
      <div ref={contentRef} className="h-full overflow-y-auto px-4 pb-24 pt-5">
        {children}
      </div>
      {bottomNav}
    </main>
  );
}
