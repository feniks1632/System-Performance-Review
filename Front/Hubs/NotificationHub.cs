// Hubs/NotificationHub.cs

using Microsoft.AspNetCore.SignalR;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Hubs
{
    public interface INotificationClient
    {
        Task ReceiveNotification(string title, string message, string type);
        Task UpdateUnreadCount(int count);
    }

    public class NotificationHub : Hub<INotificationClient>
    {
        private readonly INotificationService _notificationService;
        private readonly IAuthService _authService;

        public NotificationHub(INotificationService notificationService, IAuthService authService)
        {
            _notificationService = notificationService;
            _authService = authService;
        }

        public override async Task OnConnectedAsync()
        {
            if (_authService.IsAuthenticated())
            {
                var user = _authService.GetCurrentUser();
                if (user != null)
                {
                    await Groups.AddToGroupAsync(Context.ConnectionId, user.Id);
                }
            }
            await base.OnConnectedAsync();
        }

        public async Task MarkAsRead(string notificationId)
        {
            if (_authService.IsAuthenticated())
            {
                await _notificationService.MarkAsReadAsync(notificationId);
                var count = await _notificationService.GetUnreadCountAsync();
                await Clients.Caller.UpdateUnreadCount(count);
            }
        }

        public async Task MarkAllAsRead()
        {
            if (_authService.IsAuthenticated())
            {
                await _notificationService.MarkAllAsReadAsync();
                await Clients.Caller.UpdateUnreadCount(0);
            }
        }
    }
}