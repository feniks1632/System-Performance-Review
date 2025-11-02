// ViewComponents/SafeNotificationBadgeViewComponent.cs
using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.ViewComponents
{
    public class SafeNotificationBadgeViewComponent : ViewComponent
    {
        private readonly INotificationService _notificationService;
        private readonly IAuthService _authService;

        public SafeNotificationBadgeViewComponent(INotificationService notificationService, IAuthService authService)
        {
            _notificationService = notificationService;
            _authService = authService;
        }

        public async Task<IViewComponentResult> InvokeAsync()
        {
            // Если пользователь не авторизован, возвращаем пустой бейдж
            if (!_authService.IsAuthenticated())
            {
                return View(new NotificationBadgeViewModel 
                { 
                    UnreadCount = 0,
                    Notifications = new List<NotificationResponse>()
                });
            }

            try
            {
                // Используем suppressAuthClear = true для предотвращения сброса авторизации
                var notifications = await _notificationService.GetNotificationsAsync(unreadOnly: true, limit: 5, suppressAuthClear: true);
                var unreadCount = await _notificationService.GetUnreadCountAsync(suppressAuthClear: true);
                
                var viewModel = new NotificationBadgeViewModel
                {
                    UnreadCount = unreadCount,
                    Notifications = notifications ?? new List<NotificationResponse>()
                };

                return View(viewModel);
            }
            catch (Exception ex)
            {
                // В случае ошибки логируем, но не ломаем страницу
                Console.WriteLine($"[SafeNotificationBadge] Error loading notifications: {ex.Message}");
                return View(new NotificationBadgeViewModel 
                { 
                    UnreadCount = 0,
                    Notifications = new List<NotificationResponse>()
                });
            }
        }
    }

    public class NotificationBadgeViewModel
    {
        public int UnreadCount { get; set; }
        public List<NotificationResponse> Notifications { get; set; } = new();
    }
}