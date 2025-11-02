// Models/ReviewModels.cs
using System.ComponentModel.DataAnnotations;
using PerformanceReviewWeb.Models;
using System.Text.Json.Serialization;

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

    public class RespondentReviewViewModel
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public List<QuestionTemplateResponse> Questions { get; set; } = new List<QuestionTemplateResponse>();
        public RespondentReviewCreateModel Review { get; set; } = new RespondentReviewCreateModel();
    }

    public class ReviewCreateViewModel
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public ReviewType ReviewType { get; set; }
        public List<QuestionTemplateResponse> Questions { get; set; } = new List<QuestionTemplateResponse>();
        public ReviewCreateModel Review { get; set; } = new ReviewCreateModel();
    }

    public class ManagerScoringViewModel
    {
        public string ReviewId { get; set; } = string.Empty;
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public string EmployeeName { get; set; } = string.Empty;
        public ReviewResponse? Review { get; set; }

        // ЗАМЕНЯЕМ PendingQuestions на ManagerQuestions
        public List<ManagerQuestion> ManagerQuestions { get; set; } = new List<ManagerQuestion>();

        public List<AnswerModel> ManagerScores { get; set; } = new List<AnswerModel>();
        public FinalReviewUpdateModel FinalReview { get; set; } = new FinalReviewUpdateModel();
    }


    public class ManagerQuestion
    {
        public string QuestionId { get; set; } = string.Empty;
        public string QuestionText { get; set; } = string.Empty;
        public int MaxScore { get; set; } = 10; // Всегда 10-балльная система
        public double Weight { get; set; } = 1.0;
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