// Services/NotificationService.cs
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Services
{
    public interface INotificationService
    {
        Task<List<NotificationResponse>> GetNotificationsAsync(bool unreadOnly = false, int limit = 50, bool suppressAuthClear = false);
        Task<int> GetUnreadCountAsync(bool suppressAuthClear = false);
        Task<bool> MarkAsReadAsync(string notificationId);
        Task<bool> MarkAllAsReadAsync();
    }

    public class NotificationService : INotificationService
    {
        private readonly IApiService _apiService;

        public NotificationService(IApiService apiService)
        {
            _apiService = apiService;
        }

        public async Task<List<NotificationResponse>> GetNotificationsAsync(bool unreadOnly = false, int limit = 50, bool suppressAuthClear = false)
        {
            try
            {
                var endpoint = $"notifications/?unread_only={unreadOnly.ToString().ToLower()}&limit={limit}";
                Console.WriteLine($"[NotificationService] Requesting: {endpoint}");

                var result = await _apiService.GetAsync<List<NotificationResponse>>(endpoint, suppressAuthClear);
                return result ?? new List<NotificationResponse>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[NotificationService] Error getting notifications: {ex.Message}");
                return new List<NotificationResponse>();
            }
        }

        public async Task<int> GetUnreadCountAsync(bool suppressAuthClear = false)
        {
            try
            {
                var response = await _apiService.GetAsync<UnreadCountResponse>("notifications/unread-count", suppressAuthClear);
                return response?.UnreadCount ?? 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[NotificationService] Error getting unread count: {ex.Message}");
                return 0;
            }
        }

        public async Task<bool> MarkAsReadAsync(string notificationId)
        {
            try
            {
                // Используем API endpoint для отметки как прочитанного
                var result = await _apiService.PutAsync<SuccessResponse>($"notifications/{notificationId}/read", new { });
                return result != null && result.Status == "success";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[NotificationService] Error marking notification as read: {ex.Message}");
                return false;
            }
        }

        public async Task<bool> MarkAllAsReadAsync()
        {
            try
            {
                // Используем API endpoint для отметки всех как прочитанных
                var result = await _apiService.PutAsync<SuccessResponse>("notifications/read-all", new { });
                return result != null && result.Status == "success";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[NotificationService] Error marking all notifications as read: {ex.Message}");
                return false;
            }
        }
    }
}