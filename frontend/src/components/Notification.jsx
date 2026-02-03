"use client";

import { createContext, useContext, useState } from "react";

const NotificationContext = createContext(undefined);

export function NotificationProvider({ children }) {
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type) => {
    const id = Date.now();
    setNotification({ message, type, id });
    setTimeout(() => {
      setNotification((current) => (current?.id === id ? null : current));
    }, 3000);
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      {notification && (
        <div className="fixed top-5 right-5 z-[100] animate-in slide-in-from-top-5 duration-300">
          <div
            className={`px-6 py-4 rounded-xl shadow-2xl border border-white/10 text-white font-medium flex items-center gap-3 ${notification.type === "success"
                ? "bg-green-600/90 backdrop-blur-md"
                : notification.type === "error"
                  ? "bg-red-600/90 backdrop-blur-md"
                  : "bg-blue-600/90 backdrop-blur-md"
              }`}
          >
            {notification.message}
          </div>
        </div>
      )}
    </NotificationContext.Provider>
  );
}

function getAlertClass(type) {
  switch (type) {
    case "success":
      return "alert-success";
    case "error":
      return "alert-error";
    case "warning":
      return "alert-warning";
    case "info":
      return "alert-info";
    default:
      return "alert-info";
  }
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error(
      "useNotification must be used within a NotificationProvider"
    );
  }
  return context;
}
