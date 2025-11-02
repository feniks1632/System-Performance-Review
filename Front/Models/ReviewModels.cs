// Models/ReviewModels.cs
using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using System.Text.Json.Serialization;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Models
{
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public enum ReviewType
    {
        [JsonPropertyName("self")]
        Self,
        
        [JsonPropertyName("manager")]
        Manager,
        
        [JsonPropertyName("potential")]
        Potential,
        
        [JsonPropertyName("respondent")]
        Respondent
    }

    public class AnswerModel
    {
        [Required]
        [JsonPropertyName("question_id")]
        public string QuestionId { get; set; } = string.Empty;

        [JsonPropertyName("answer")]
        public string? Answer { get; set; }

        [JsonPropertyName("score")]
        public double? Score { get; set; }

        [JsonPropertyName("selected_option")]
        public string? SelectedOption { get; set; }

        // Дополнительное свойство для биндинга чекбоксов
        [JsonIgnore]
        public List<string>? SelectedOptions { get; set; }
    }

    public class ReviewCreateModel
    {
        [Required]
        [JsonPropertyName("goal_id")]
        public string GoalId { get; set; } = string.Empty;
        
        [Required]
        [JsonPropertyName("review_type")]
        public ReviewType ReviewType { get; set; }
        
        [Required]
        [JsonPropertyName("answers")]
        public List<AnswerModel> Answers { get; set; } = new List<AnswerModel>();
    }

    public class RespondentReviewCreateModel
    {
        [Required]
        [JsonPropertyName("goal_id")]
        public string GoalId { get; set; } = string.Empty;
        
        [Required]
        [JsonPropertyName("answers")]
        public List<AnswerModel> Answers { get; set; } = new List<AnswerModel>();
        
        [JsonPropertyName("comments")]
        public string? Comments { get; set; }
    }

    public class FinalReviewUpdateModel
    {
        [Required]
        [JsonPropertyName("final_rating")]
        public string FinalRating { get; set; } = string.Empty;
        
        [Required]
        [JsonPropertyName("final_feedback")]
        public string FinalFeedback { get; set; } = string.Empty;
    }

    public class ReviewResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;
        
        [JsonPropertyName("goal_id")]
        public string GoalId { get; set; } = string.Empty;
        
        [JsonPropertyName("reviewer_id")]
        public string ReviewerId { get; set; } = string.Empty;
        
        [JsonPropertyName("review_type")]
        public ReviewType ReviewType { get; set; }
        
        [JsonPropertyName("calculated_score")]
        public double? CalculatedScore { get; set; }
        
        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; }
        
        [JsonPropertyName("final_rating")]
        public string? FinalRating { get; set; }
        
        [JsonPropertyName("final_feedback")]
        public string? FinalFeedback { get; set; }
    }

    public class ReviewResponseWithAnswers : ReviewResponse
    {
        [JsonPropertyName("self_evaluation_answers")]
        public List<Dictionary<string, object>>? SelfEvaluationAnswers { get; set; }
        
        [JsonPropertyName("manager_evaluation_answers")]
        public List<Dictionary<string, object>>? ManagerEvaluationAnswers { get; set; }
        
        [JsonPropertyName("potential_evaluation_answers")]
        public List<Dictionary<string, object>>? PotentialEvaluationAnswers { get; set; }
    }

    public class RespondentReviewResponse
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;
        
        [JsonPropertyName("goal_id")]
        public string GoalId { get; set; } = string.Empty;
        
        [JsonPropertyName("respondent_id")]
        public string RespondentId { get; set; } = string.Empty;
        
        [JsonPropertyName("respondent_name")]
        public string? RespondentName { get; set; }
        
        [JsonPropertyName("answers")]
        public List<AnswerModel> Answers { get; set; } = new List<AnswerModel>();
        
        [JsonPropertyName("comments")]
        public string? Comments { get; set; }
        
        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; }
    }

    // ДОБАВЬТЕ ЭТОТ КЛАСС
    public class RespondentReviewViewModel
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public List<QuestionTemplateResponse> Questions { get; set; } = new List<QuestionTemplateResponse>();
        public RespondentReviewCreateModel Review { get; set; } = new RespondentReviewCreateModel();
    }

    // ДОБАВЬТЕ ЭТОТ КЛАСС (если используется в ReviewsController)
    public class ReviewCreateViewModel
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public ReviewType ReviewType { get; set; }
        public List<QuestionTemplateResponse> Questions { get; set; } = new List<QuestionTemplateResponse>();
        public ReviewCreateModel Review { get; set; } = new ReviewCreateModel();
    }

    public class QuestionTemplateResponse
    {
        public string Id { get; set; } = string.Empty;
        public string QuestionText { get; set; } = string.Empty;
        public string QuestionType { get; set; } = string.Empty;
        public string? Section { get; set; }
        public double Weight { get; set; } = 1.0;
        public int MaxScore { get; set; } = 5;
        public int OrderIndex { get; set; }
        public string? TriggerWords { get; set; }
        public string? OptionsJson { get; set; }
        public bool RequiresManagerScoring { get; set; }
        public bool IsActive { get; set; }
        public DateTime CreatedAt { get; set; }

        // ИСПРАВЛЕННАЯ логика десериализации
        public List<QuestionOption>? Options
        {
            get
            {
                if (string.IsNullOrEmpty(OptionsJson) || OptionsJson == "null")
                    return null;

                try
                {
                    var options = System.Text.Json.JsonSerializer.Deserialize<List<QuestionOption>>(
                        OptionsJson,
                        new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        });

                    // ДЕБАГ: выводим в консоль для диагностики
                    Console.WriteLine($"[QuestionTemplate] Question: {QuestionText}");
                    Console.WriteLine($"[QuestionTemplate] Type: {QuestionType}");
                    Console.WriteLine($"[QuestionTemplate] OptionsJson: {OptionsJson}");
                    Console.WriteLine($"[QuestionTemplate] Deserialized options count: {options?.Count ?? 0}");

                    return options;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[QuestionTemplate] Error deserializing options for '{QuestionText}': {ex.Message}");
                    Console.WriteLine($"[QuestionTemplate] OptionsJson: {OptionsJson}");
                    return null;
                }
            }
        }
    }

    public class QuestionTemplateCreateModel
    {
        [Required(ErrorMessage = "Текст вопроса обязателен")]
        [Display(Name = "Текст вопроса")]
        public string QuestionText { get; set; } = string.Empty;

        [Required(ErrorMessage = "Тип вопроса обязателен")]
        [Display(Name = "Тип вопроса")]
        public string QuestionType { get; set; } = string.Empty;

        [Display(Name = "Раздел")]
        public string? Section { get; set; }

        [Required(ErrorMessage = "Вес вопроса обязателен")]
        [Range(0.1, 10.0, ErrorMessage = "Вес должен быть от 0.1 до 10.0")]
        [Display(Name = "Вес вопроса")]
        public double Weight { get; set; } = 1.0;

        [Required(ErrorMessage = "Максимальный балл обязателен")]
        [Range(1, 100, ErrorMessage = "Максимальный балл должен быть от 1 до 100")]
        [Display(Name = "Максимальный балл")]
        public int MaxScore { get; set; } = 5;

        [Required(ErrorMessage = "Порядковый номер обязателен")]
        [Display(Name = "Порядковый номер")]
        public int OrderIndex { get; set; }

        [Display(Name = "Триггерные слова (через запятую)")]
        public string? TriggerWords { get; set; }

        [Display(Name = "Опции (JSON)")]
        public string? OptionsJson { get; set; }

        [Display(Name = "Требует оценки руководителя")]
        public bool RequiresManagerScoring { get; set; }
    }

    public class QuestionTemplateEditModel
    {
        [Required(ErrorMessage = "Текст вопроса обязателен")]
        [Display(Name = "Текст вопроса")]
        public string QuestionText { get; set; } = string.Empty;

        [Required(ErrorMessage = "Тип вопроса обязателен")]
        [Display(Name = "Тип вопроса")]
        public string QuestionType { get; set; } = string.Empty;

        [Display(Name = "Раздел")]
        public string? Section { get; set; }

        [Required(ErrorMessage = "Вес вопроса обязателен")]
        [Range(0.1, 10.0, ErrorMessage = "Вес должен быть от 0.1 до 10.0")]
        [Display(Name = "Вес вопроса")]
        public double Weight { get; set; } = 1.0;

        [Required(ErrorMessage = "Максимальный балл обязателен")]
        [Range(1, 100, ErrorMessage = "Максимальный балл должен быть от 1 до 100")]
        [Display(Name = "Максимальный балл")]
        public int MaxScore { get; set; } = 5;

        [Required(ErrorMessage = "Порядковый номер обязателен")]
        [Display(Name = "Порядковый номер")]
        public int OrderIndex { get; set; }

        [Display(Name = "Триггерные слова (через запятую)")]
        public string? TriggerWords { get; set; }

        [Display(Name = "Опции (JSON)")]
        public string? OptionsJson { get; set; }

        [Display(Name = "Требует оценки руководителя")]
        public bool RequiresManagerScoring { get; set; }
    }

    public class QuestionOption
    {
        public string Id { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public double Value { get; set; }
        public int OrderIndex { get; set; }
    }

    public class ManagerScoringViewModel
    {
        public string ReviewId { get; set; } = string.Empty;
        public ReviewResponse? Review { get; set; }
        public List<PendingQuestion> PendingQuestions { get; set; } = new List<PendingQuestion>();
        public FinalReviewUpdateModel FinalReview { get; set; } = new FinalReviewUpdateModel();
        public List<AnswerModel> ManagerScores { get; set; } = new List<AnswerModel>();
    }

    public class PendingQuestion
    {
        public string QuestionId { get; set; } = string.Empty;
        public string QuestionText { get; set; } = string.Empty;
        public string? Answer { get; set; }
        public double? CurrentScore { get; set; }
        public string? QuestionType { get; set; }
        public double Weight { get; set; } = 1.0;
        public int MaxScore { get; set; } = 10;
        public string? Section { get; set; }
    }

    public class ManagerScoreRequest
    {
        public string QuestionId { get; set; } = string.Empty;
        public double Score { get; set; }
        public string? Feedback { get; set; }
    }
}