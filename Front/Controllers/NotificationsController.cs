// Controllers/NotificationsController.cs

using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("notifications")]
    public class NotificationsController : Controller  // ← Изменили на Controller (не ControllerBase)
    {
        private readonly INotificationService _notificationService;
        private readonly IAuthService _authService;

        public NotificationsController(INotificationService notificationService, IAuthService authService)
        {
            _notificationService = notificationService;
            _authService = authService;
        }

        [HttpGet]
        public async Task<IActionResult> Index(bool unread_only = false)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            // Получаем уведомления для отображения на странице
            var notifications = await _notificationService.GetNotificationsAsync(unread_only, 50);
            
            ViewBag.User = _authService.GetCurrentUser();
            ViewBag.UnreadOnly = unread_only;
            
            return View(notifications);
        }

        [HttpPost("mark-read/{id}")]
        public async Task<IActionResult> MarkAsRead(string id)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false });

            var success = await _notificationService.MarkAsReadAsync(id);
            return Json(new { success });
        }

        [HttpPost("mark-all-read")]
        public async Task<IActionResult> MarkAllAsRead()
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false });

            var success = await _notificationService.MarkAllAsReadAsync();
            return Json(new { success });
        }

        [HttpGet("unread-count")]
        public async Task<IActionResult> GetUnreadCount()
        {
            if (!_authService.IsAuthenticated())
                return Json(new { count = 0 });

            var count = await _notificationService.GetUnreadCountAsync();
            return Json(new { count });
        }
    }

    // DTO классы для ответов
    public class NotificationResponse
    {
        public string Id { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string NotificationType { get; set; } = string.Empty;
        public bool IsRead { get; set; }
        public DateTime CreatedAt { get; set; }
        public string RelatedEntityType { get; set; } = string.Empty;
        public string RelatedEntityId { get; set; } = string.Empty;
    }

    public class StatusResponse
    {
        public string Status { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
    }

    public class UnreadCountResponse
    {
        public int UnreadCount { get; set; }
    }

    public class ValidationErrorResponse
    {
        public ValidationErrorDetail[] Detail { get; set; } = Array.Empty<ValidationErrorDetail>();
    }

    public class ValidationErrorDetail
    {
        public string[] Loc { get; set; } = Array.Empty<string>();
        public string Msg { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
    }
}