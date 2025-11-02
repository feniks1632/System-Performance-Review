// Models/NotificationModels.cs

using System.Text.Json.Serialization;

namespace PerformanceReviewWeb.Models
{
    public class NotificationResponse
    {
        public string Id { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string NotificationType { get; set; } = string.Empty;
        public bool IsRead { get; set; }
        public DateTime CreatedAt { get; set; }
        public string? RelatedEntityType { get; set; }
        public string? RelatedEntityId { get; set; }
    }

    public class UnreadCountResponse
    {
        public int UnreadCount { get; set; }
    }

    public class ApiResponse<T>
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;
        
        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;
        
        [JsonPropertyName("data")]
        public T? Data { get; set; }
    }

    public class SuccessResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;
    }
}