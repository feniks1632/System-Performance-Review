// Services/ReviewService.cs
using System.Text.Json;
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Services
{
    public interface IReviewService
    {
        Task<List<ReviewResponse>> GetReviewsAsync();
        Task<ReviewResponse?> GetReviewAsync(string id);
        Task<ReviewResponseWithAnswers?> GetReviewWithAnswersAsync(string id);
        Task<ReviewResponse?> CreateReviewAsync(ReviewCreateModel model);
        Task<ReviewResponse?> UpdateFinalReviewAsync(string reviewId, FinalReviewUpdateModel model);
        Task<RespondentReviewResponse?> CreateRespondentReviewAsync(RespondentReviewCreateModel model);
        Task<RespondentReviewResponse?> GetRespondentReviewAsync(string reviewId);
        Task<List<ReviewResponse>> GetReviewsByGoalAsync(string goalId);
        Task<List<QuestionTemplateResponse>> GetQuestionTemplatesAsync(string? questionType = null, string? section = null);
        Task<SuccessResponse?> ScoreManagerQuestionsAsync(string reviewId, List<AnswerModel> scores);
        Task<List<Dictionary<string, object>>?> GetPendingManagerScoresAsync(string reviewId);
        Task<List<ReviewResponse>?> GetPendingManagerReviewsAsync();
        Task<List<ReviewResponse>> GetReviewsByReviewerAsync(string reviewerId);
    Task<List<ReviewResponse>> GetReviewsByGoalAndReviewerAsync(string goalId, string reviewerId);
    }

    public class ReviewService : IReviewService
    {
        private readonly IApiService _apiService;

        public ReviewService(IApiService apiService)
        {
            _apiService = apiService;
        }

        public async Task<List<ReviewResponse>> GetReviewsAsync()
        {
            return await _apiService.GetAsync<List<ReviewResponse>>("reviews/") ?? new List<ReviewResponse>();
        }

        public async Task<ReviewResponse?> GetReviewAsync(string id)
        {
            return await _apiService.GetAsync<ReviewResponse>($"reviews/{id}");
        }

        public async Task<ReviewResponseWithAnswers?> GetReviewWithAnswersAsync(string id)
        {
            return await _apiService.GetAsync<ReviewResponseWithAnswers>($"reviews/{id}");
        }

        public async Task<ReviewResponse?> CreateReviewAsync(ReviewCreateModel model)
        {
            try
            {
                var requestData = new Dictionary<string, object>
                {
                    ["goal_id"] = model.GoalId,
                    ["review_type"] = model.ReviewType.ToString().ToLowerInvariant(),
                    ["answers"] = model.Answers.Where(a =>
                        !string.IsNullOrEmpty(a.Answer) ||
                        a.Score.HasValue ||
                        !string.IsNullOrEmpty(a.SelectedOption)
                    ).Select(a =>
                    {
                        var answerData = new Dictionary<string, object?>
                        {
                            ["question_id"] = a.QuestionId
                        };

                        // Обработка текстового ответа
                        if (!string.IsNullOrEmpty(a.Answer))
                        {
                            answerData["answer"] = a.Answer;
                        }

                        // Обработка числовой оценки
                        if (a.Score.HasValue)
                        {
                            answerData["score"] = a.Score.Value;
                        }

                        // Обработка выбранных опций
                        if (!string.IsNullOrEmpty(a.SelectedOption))
                        {
                            answerData["selected_option"] = a.SelectedOption;
                        }
                        // Обработка множественного выбора из SelectedOptions
                        else if (a.SelectedOptions != null && a.SelectedOptions.Any())
                        {
                            answerData["selected_option"] = string.Join(",", a.SelectedOptions);
                        }

                        return answerData;
                    }).ToList()
                };

                Console.WriteLine($"[ReviewService] Creating {model.ReviewType} review for goal {model.GoalId}");
                var json = JsonSerializer.Serialize(requestData, new JsonSerializerOptions { WriteIndented = true });
                Console.WriteLine($"[ReviewService] Request data: {json}");

                return await _apiService.PostAsync<ReviewResponse>("reviews/", requestData);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error creating review: {ex.Message}");
                return null;
            }
        }

        public async Task<ReviewResponse?> UpdateFinalReviewAsync(string reviewId, FinalReviewUpdateModel model)
        {
            try
            {
                Console.WriteLine($"[ReviewService] Updating final review {reviewId} with rating: {model.FinalRating}");

                var requestData = new Dictionary<string, object>
                {
                    ["final_rating"] = model.FinalRating,
                    ["final_feedback"] = model.FinalFeedback
                };

                var result = await _apiService.PutAsync<ReviewResponse>($"reviews/{reviewId}/final", requestData);

                if (result != null)
                {
                    Console.WriteLine($"[ReviewService] Successfully updated final review {reviewId}");
                }
                else
                {
                    Console.WriteLine($"[ReviewService] Failed to update final review {reviewId}");
                }

                return result;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error updating final review {reviewId}: {ex.Message}");
                return null;
            }
        }

        public async Task<RespondentReviewResponse?> CreateRespondentReviewAsync(RespondentReviewCreateModel model)
        {
            try
            {
                // Аналогично для респондентов
                var requestData = new Dictionary<string, object>
                {
                    ["goal_id"] = model.GoalId,
                    ["answers"] = model.Answers.Select(a => new Dictionary<string, object>
                    {
                        ["question_id"] = a.QuestionId,
                        ["answer"] = a.Answer ?? string.Empty,
                        ["score"] = a.Score ?? 0,
                        ["selected_option"] = a.SelectedOption ?? string.Empty
                    }).ToList(),
                    ["comments"] = model.Comments ?? string.Empty
                };

                var json = System.Text.Json.JsonSerializer.Serialize(requestData, new JsonSerializerOptions
                {
                    WriteIndented = true
                });
                Console.WriteLine($"[ReviewService] Sending respondent request: {json}");

                return await _apiService.PostAsync<RespondentReviewResponse>("reviews/respondent", requestData);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error creating respondent review: {ex.Message}");
                return null;
            }
        }

        public async Task<RespondentReviewResponse?> GetRespondentReviewAsync(string reviewId)
        {
            return await _apiService.GetAsync<RespondentReviewResponse>($"reviews/respondent/{reviewId}");
        }

        public async Task<List<ReviewResponse>> GetReviewsByGoalAsync(string goalId)
        {
            return await _apiService.GetAsync<List<ReviewResponse>>($"reviews/goal/{goalId}") ?? new List<ReviewResponse>();
        }

        public async Task<List<QuestionTemplateResponse>> GetQuestionTemplatesAsync(string? questionType = null, string? section = null)
        {
            var queryParams = new List<string>();
            if (!string.IsNullOrEmpty(questionType))
                queryParams.Add($"question_type={Uri.EscapeDataString(questionType)}");
            if (!string.IsNullOrEmpty(section))
                queryParams.Add($"section={Uri.EscapeDataString(section)}");

            var queryString = queryParams.Any() ? $"?{string.Join("&", queryParams)}" : "";
            return await _apiService.GetAsync<List<QuestionTemplateResponse>>($"question-templates/{queryString}") ?? new List<QuestionTemplateResponse>();
        }

        public async Task<SuccessResponse?> ScoreManagerQuestionsAsync(string reviewId, List<AnswerModel> scores)
        {
            try
            {
                Console.WriteLine($"[ReviewService] Scoring {scores.Count} manager questions for review: {reviewId}");

                // Преобразуем AnswerModel в формат для API руководителя
                var requestData = scores.Where(score => score.Score.HasValue)
                                       .Select(score => new Dictionary<string, object>
                                       {
                                           ["question_id"] = score.QuestionId,
                                           ["score"] = score.Score.Value, // Обязательная оценка 1-10
                                           ["answer"] = score.Answer ?? string.Empty, // Комментарий руководителя
                                           ["selected_option"] = score.SelectedOption ?? string.Empty
                                       }).ToList();

                if (!requestData.Any())
                {
                    Console.WriteLine($"[ReviewService] No valid scores to send for review {reviewId}");
                    return new SuccessResponse { Status = "success", Message = "No scores to update" };
                }

                Console.WriteLine($"[ReviewService] Sending {requestData.Count} manager scores to API");

                // Используем правильный endpoint из спецификации API
                var result = await _apiService.PostAsync<SuccessResponse>(
                    $"/api/v1/reviews/{reviewId}/score-manager-questions",
                    requestData
                );

                if (result != null)
                {
                    Console.WriteLine($"[ReviewService] Successfully scored manager questions for review {reviewId}: {result.Status} - {result.Message}");
                }
                else
                {
                    Console.WriteLine($"[ReviewService] Failed to score manager questions for review {reviewId} - null response");
                }

                return result;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error scoring manager questions for {reviewId}: {ex.Message}");
                return new SuccessResponse { Status = "error", Message = ex.Message };
            }
        }

        public async Task<List<Dictionary<string, object>>?> GetPendingManagerScoresAsync(string reviewId)
        {
            try
            {
                Console.WriteLine($"[ReviewService] Getting pending manager scores for review: {reviewId}");

                var result = await _apiService.GetAsync<List<Dictionary<string, object>>>($"reviews/{reviewId}/pending-manager-scores");

                Console.WriteLine($"[ReviewService] Found {result?.Count ?? 0} pending questions for review {reviewId}");

                return result;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error getting pending manager scores for {reviewId}: {ex.Message}");
                return null;
            }
        }

        public async Task<List<ReviewResponse>?> GetPendingManagerReviewsAsync()
        {
            try
            {
                return await _apiService.GetAsync<List<ReviewResponse>>("reviews/pending-manager-scores") ?? new List<ReviewResponse>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error getting pending manager reviews: {ex.Message}");
                return new List<ReviewResponse>();
            }
        }

        public async Task<List<ReviewResponse>> GetReviewsByReviewerAsync(string reviewerId)
        {
            try
            {
                // Получаем все оценки и фильтруем по reviewer_id
                var allReviews = await GetReviewsAsync();
                return allReviews?
                    .Where(r => r.ReviewerId == reviewerId)
                    .ToList() ?? new List<ReviewResponse>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error getting reviews for reviewer {reviewerId}: {ex.Message}");
                return new List<ReviewResponse>();
            }
        }

        public async Task<List<ReviewResponse>> GetReviewsByGoalAndReviewerAsync(string goalId, string reviewerId)
        {
            try
            {
                // Получаем оценки по цели и фильтруем по reviewer_id
                var goalReviews = await GetReviewsByGoalAsync(goalId);
                return goalReviews?
                    .Where(r => r.ReviewerId == reviewerId)
                    .ToList() ?? new List<ReviewResponse>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewService] Error getting reviews for goal {goalId} and reviewer {reviewerId}: {ex.Message}");
                return new List<ReviewResponse>();
            }
        }
    }
}