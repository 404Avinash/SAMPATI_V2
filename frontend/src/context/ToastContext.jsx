import React, { createContext, useContext, useState, useCallback, useMemo, useRef } from "react";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const counterRef = useRef(0);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ type = "info", message, duration = 4000, title }) => {
      counterRef.current += 1;
      const id = `toast_${Date.now()}_${counterRef.current}`;
      const newToast = { id, type, message, duration, title, createdAt: Date.now() };

      setToasts((prev) => [...prev.slice(-6), newToast]);

      if (duration && duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }

      return id;
    },
    [removeToast]
  );

  const toast = useMemo(
    () => ({
      success: (message, duration = 4000, title) =>
        showToast({ type: "success", message, duration, title: title || "Success" }),
      error: (message, duration = 5000, title) =>
        showToast({ type: "error", message, duration, title: title || "Error" }),
      info: (message, duration = 4000, title) =>
        showToast({ type: "info", message, duration, title: title || "Notification" }),
      warning: (message, duration = 4500, title) =>
        showToast({ type: "warning", message, duration, title: title || "Warning" }),
    }),
    [showToast]
  );

  const value = useMemo(
    () => ({
      toasts,
      showToast,
      removeToast,
      toast,
    }),
    [toasts, showToast, removeToast, toast]
  );

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Fallback safe dummy if rendered outside provider to avoid crashes
    return {
      toasts: [],
      showToast: () => {},
      removeToast: () => {},
      toast: {
        success: (msg) => console.log("[Toast success]:", msg),
        error: (msg) => console.error("[Toast error]:", msg),
        info: (msg) => console.log("[Toast info]:", msg),
        warning: (msg) => console.warn("[Toast warning]:", msg),
      },
    };
  }
  return context;
}

export default ToastContext;
