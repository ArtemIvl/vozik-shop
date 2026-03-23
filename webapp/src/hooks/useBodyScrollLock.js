import { useLayoutEffect } from "react";

export function useBodyScrollLock(active) {
  useLayoutEffect(() => {
    void active;
    return undefined;
  }, [active]);
}
