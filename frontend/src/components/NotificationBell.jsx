import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { useUnreadCount, useNotifications, useMarkRead } from "../hooks/useNotifications.js";
import { useAuth } from "../hooks/useAuth.js";

export default function NotificationBell() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const { data: count = 0 } = useUnreadCount();
  const { data: notifications = [] } = useNotifications({ size: 10 });
  const { mutate: markRead } = useMarkRead();

  if (!user) return null;

  const handleOpen = () => {
    setOpen(!open);
    if (!open && count > 0) {
      const unreadIds = notifications
        .filter((n) => !n.is_read)
        .map((n) => n.notification_id);
      if (unreadIds.length) markRead(unreadIds);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleOpen}
        className="relative p-2 rounded-full hover:bg-gray-100 transition-colors"
        aria-label="Notifications"
      >
        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-10 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-40 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 font-semibold text-gray-900">
              Notifications
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-sm text-gray-500 px-4 py-6 text-center">No notifications yet</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.notification_id}
                    className={`px-4 py-3 text-sm border-b border-gray-50 ${!n.is_read ? "bg-blue-50" : ""}`}
                  >
                    <p className="text-gray-800">{n.message}</p>
                    <p className="text-gray-400 text-xs mt-1">
                      {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
