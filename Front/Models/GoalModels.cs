// Models/GoalModels.cs

using PerformanceReviewWeb.Validators;
using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace PerformanceReviewWeb.Models
{
    public class GoalStepCreateModel
    {
        [Required(ErrorMessage = "Название подпункта обязательно")]
        public string Title { get; set; } = string.Empty;
        public string? Description { get; set; }
        [Range(1, 10, ErrorMessage = "Порядок должен быть от 1 до 10")]
        public int OrderIndex { get; set; }
    }

    public class GoalStepUpdateModel
    {
        public string? Title { get; set; }
        public string? Description { get; set; }
        public bool? IsCompleted { get; set; }
        public int? OrderIndex { get; set; }
    }

    public class GoalStepResponse
    {
        public string Id { get; set; } = string.Empty;
        public string GoalId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string? Description { get; set; }
        public bool IsCompleted { get; set; }
        public int OrderIndex { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    public class GoalCreateModel
    {
        [Required(ErrorMessage = "Название цели обязательно")]
        [StringLength(200, ErrorMessage = "Название не должно превышать 200 символов")]
        public string Title { get; set; } = string.Empty;

        [Required(ErrorMessage = "Описание цели обязательно")]
        public string Description { get; set; } = string.Empty;

        [Required(ErrorMessage = "Ожидаемый результат обязателен")]
        public string ExpectedResult { get; set; } = string.Empty;

        [Required(ErrorMessage = "Дедлайн обязателен")]
        [FutureDate(ErrorMessage = "Дедлайн должен быть в будущем")]
        public DateTime Deadline { get; set; }

        [Url(ErrorMessage = "Укажите корректную ссылку")]
        public string? TaskLink { get; set; }

        [Display(Name = "Респонденты")]
        [Required(ErrorMessage = "Укажите хотя бы одного респондента")]
        public string RespondentIds { get; set; } = string.Empty;
        // Helper property to convert string to list for API
        [JsonIgnore]
        public List<string> RespondentIdsList =>
            string.IsNullOrEmpty(RespondentIds)
                ? new List<string>()
                : RespondentIds.Split(',', StringSplitOptions.RemoveEmptyEntries)
                              .Select(id => id.Trim())
                              .Where(id => !string.IsNullOrEmpty(id))
                              .ToList();

        [MaxSteps(3, ErrorMessage = "Максимум можно добавить 3 подпункта")]
        public List<GoalStepCreateModel>? Steps { get; set; } = new();
    }

    public class GoalResponse
    {
        public string Id { get; set; } = string.Empty;
        public string EmployeeId { get; set; } = string.Empty;
        public string Title { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string ExpectedResult { get; set; } = string.Empty;
        public DateTime Deadline { get; set; }
        public string? TaskLink { get; set; }
        public string Status { get; set; } = "active";
        public DateTime CreatedAt { get; set; }
        public string? EmployeeName { get; set; }
        public List<GoalStepResponse> Steps { get; set; } = new List<GoalStepResponse>();
        public List<string> RespondentNames { get; set; } = new List<string>();
    }

    public class GoalStatusUpdateModel
    {
        [Required]
        public string Status { get; set; } = string.Empty;
    }
}