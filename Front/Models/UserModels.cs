// Models/UserModels.cs

using System.ComponentModel.DataAnnotations;

namespace PerformanceReviewWeb.Models
{
    public class AssignManagerModel
    {
        [Required(ErrorMessage = "ID пользователя обязателен")]
        public string UserId { get; set; } = string.Empty;

        [Required(ErrorMessage = "ID руководителя обязателен")]
        public string ManagerId { get; set; } = string.Empty;
    }
    
    public class UserProfileViewModel
    {
        public string Id { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string FullName { get; set; } = string.Empty;
        public bool IsManager { get; set; }
        public bool IsActive { get; set; }
        public string? ManagerId { get; set; }
        public string? ManagerName { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}