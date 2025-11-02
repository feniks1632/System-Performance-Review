// Models/QuestionTemplateModels.cs
using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PerformanceReviewWeb.Models
{
    public class QuestionTemplateResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("question_text")]
        public string QuestionText { get; set; } = string.Empty;

        [JsonPropertyName("question_type")]
        public string QuestionType { get; set; } = string.Empty;

        [JsonPropertyName("section")]
        public string? Section { get; set; }

        [JsonPropertyName("weight")]
        public double Weight { get; set; } = 1.0;

        [JsonPropertyName("max_score")]
        public int MaxScore { get; set; } = 5;

        [JsonPropertyName("order_index")]
        public int OrderIndex { get; set; }

        [JsonPropertyName("trigger_words")]
        public string? TriggerWords { get; set; }

        [JsonPropertyName("options_json")]
        public string? OptionsJson { get; set; }

        [JsonPropertyName("requires_manager_scoring")]
        public bool RequiresManagerScoring { get; set; }

        [JsonPropertyName("is_active")]
        public bool IsActive { get; set; }

        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; }

        public List<QuestionOption>? Options
        {
            get
            {
                if (string.IsNullOrEmpty(OptionsJson) || OptionsJson == "null")
                    return null;

                try
                {
                    var options = JsonSerializer.Deserialize<List<QuestionOption>>(
                        OptionsJson,
                        new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        });
                    return options;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[QuestionTemplate] Error deserializing options for '{QuestionText}': {ex.Message}");
                    return null;
                }
            }
        }
    }

    public class QuestionOption
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        [JsonPropertyName("value")]
        public double Value { get; set; }

        [JsonPropertyName("order_index")]
        public int OrderIndex { get; set; }
    }

    public class QuestionTemplateCreateModel
    {
        [Required(ErrorMessage = "Текст вопроса обязателен")]
        public string QuestionText { get; set; } = string.Empty;

        [Required(ErrorMessage = "Тип вопроса обязателен")]
        public string QuestionType { get; set; } = string.Empty;

        [Required(ErrorMessage = "Раздел обязателен")]
        public string Section { get; set; } = string.Empty;

        [Range(0.1, 10.0, ErrorMessage = "Вес должен быть от 0.1 до 10.0")]
        public decimal Weight { get; set; }

        [Range(1, 100, ErrorMessage = "Максимальный балл должен быть от 1 до 100")]
        public int MaxScore { get; set; }

        [Range(0, 100, ErrorMessage = "Порядковый номер должен быть от 0 до 100")]
        public int OrderIndex { get; set; }

        public string? TriggerWords { get; set; }
        public string? OptionsJson { get; set; }
        public bool RequiresManagerScoring { get; set; }
    }

    public class QuestionTemplateEditModel
    {
        public string Id { get; set; } = string.Empty;

        [Required(ErrorMessage = "Текст вопроса обязателен")]
        public string QuestionText { get; set; } = string.Empty;

        [Required(ErrorMessage = "Тип вопроса обязателен")]
        public string QuestionType { get; set; } = string.Empty;

        [Required(ErrorMessage = "Раздел обязателен")]
        public string Section { get; set; } = string.Empty;

        [Range(0.1, 10.0, ErrorMessage = "Вес должен быть от 0.1 до 10.0")]
        public decimal Weight { get; set; }

        [Range(1, 100, ErrorMessage = "Максимальный балл должен быть от 1 до 100")]
        public int MaxScore { get; set; }

        [Range(0, 100, ErrorMessage = "Порядковый номер должен быть от 0 до 100")]
        public int OrderIndex { get; set; }

        public string? TriggerWords { get; set; }
        public string? OptionsJson { get; set; }
        public bool RequiresManagerScoring { get; set; }
    }

    public class QuestionTemplateUpdateRequest
    {
        public string QuestionText { get; set; } = string.Empty;
        public string QuestionType { get; set; } = string.Empty;
        public string Section { get; set; } = string.Empty;
        public decimal Weight { get; set; }
        public int MaxScore { get; set; }
        public int OrderIndex { get; set; }
        public string? TriggerWords { get; set; }
        public string? OptionsJson { get; set; }
        public bool RequiresManagerScoring { get; set; }
    }

    public class QuestionTemplateCreateRequest
    {
        public string QuestionText { get; set; } = string.Empty;
        public string QuestionType { get; set; } = string.Empty;
        public string Section { get; set; } = string.Empty;
        public decimal Weight { get; set; }
        public int MaxScore { get; set; }
        public int OrderIndex { get; set; }
        public string? TriggerWords { get; set; }
        public string? OptionsJson { get; set; }
        public bool RequiresManagerScoring { get; set; }
    }
}