// ViewComponents/SafeNotificationsViewComponent.cs
using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.ViewComponents
{
    public class SafeNotificationsViewComponent : ViewComponent
    {
        private readonly INotificationService _notificationService;
        private readonly IAuthService _authService;

        public SafeNotificationsViewComponent(INotificationService notificationService, IAuthService authService)
        {
            _notificationService = notificationService;
            _authService = authService;
        }

        public async Task<IViewComponentResult> InvokeAsync()
        {
            if (!_authService.IsAuthenticated())
            {
                return Content(string.Empty); // Пустой результат если не авторизован
            }

            try
            {
                // Используем suppressAuthClear = true чтобы не сбрасывать авторизацию при 401
                var notifications = await _notificationService.GetNotificationsAsync(suppressAuthClear: true);
                var unreadCount = await _notificationService.GetUnreadCountAsync(suppressAuthClear: true);
                
                ViewBag.UnreadCount = unreadCount;
                return View(notifications);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[SafeNotifications] Error: {ex.Message}");
                // В случае ошибки возвращаем пустые данные, но не ломаем страницу
                ViewBag.UnreadCount = 0;
                return View(new List<NotificationResponse>());
            }
        }
    }
}