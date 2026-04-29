import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import notificationApi from "../services/notificationApi.js";
import { useAuth } from "./useAuth.js";

export function useUnreadCount() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationApi.get("/unread-count").then((r) => r.data.count),
    enabled: !!user,
    refetchInterval: 30_000,
  });
}

export function useNotifications(params = {}) {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["notifications", params],
    queryFn: () => notificationApi.get("", { params }).then((r) => r.data),
    enabled: !!user,
  });
}

export function useMarkRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ids) =>
      notificationApi.post("/read", { notification_ids: ids }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
