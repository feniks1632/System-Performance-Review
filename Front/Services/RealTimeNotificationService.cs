// Services/RealTimeNotificationService.cs

using Microsoft.AspNetCore.SignalR;
using PerformanceReviewWeb.Hubs;

namespace PerformanceReviewWeb.Services
{
    public interface IRealTimeNotificationService
    {
        Task SendNotificationAsync(string userId, string title, string message, string type);
    }

    public class RealTimeNotificationService : IRealTimeNotificationService
    {
        private readonly IHubContext<NotificationHub, INotificationClient> _hubContext;

        public RealTimeNotificationService(IHubContext<NotificationHub, INotificationClient> hubContext)
        {
            _hubContext = hubContext;
        }

        public async Task SendNotificationAsync(string userId, string title, string message, string type)
        {
            await _hubContext.Clients.Group(userId).ReceiveNotification(title, message, type);
        }
    }
}