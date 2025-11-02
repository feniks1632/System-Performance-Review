using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("analytics")]
    public class AnalyticsController : Controller
    {
        private readonly IApiService _apiService;
        private readonly IAuthService _authService;
        private readonly IReviewService _reviewService;

        public AnalyticsController(IApiService apiService, IAuthService authService, IReviewService reviewService)
        {
            _apiService = apiService;
            _authService = authService;
            _reviewService = reviewService;
        }

        [HttpGet]
        public async Task<IActionResult> Index()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var user = _authService.GetCurrentUser();
            var analytics = await _apiService.GetAsync<EmployeeSummaryResponse>($"analytics/employee/{user?.Id}/summary");

            ViewBag.User = user;
            return View(analytics ?? new EmployeeSummaryResponse());
        }

        [HttpGet("goal/{goalId}")]
        public async Task<IActionResult> GoalAnalytics(string goalId)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            // Получаем аналитику цели
            var analytics = await _apiService.GetAsync<GoalAnalyticsResponse>($"analytics/goal/{goalId}");
            if (analytics == null)
            {
                TempData["Error"] = "Аналитика для цели не найдена";
                return RedirectToAction("Index");
            }

            // Получаем завершенные оценки для этой цели, чтобы найти final_rating и final_feedback
            var reviews = await _reviewService.GetReviewsByGoalAsync(goalId);
            var completedReview = reviews?.FirstOrDefault(r => !string.IsNullOrEmpty(r.FinalRating));
            
            if (completedReview != null)
            {
                // Если есть завершенная оценка, добавляем данные в модель аналитики
                analytics.FinalRating = completedReview.FinalRating ?? "No rating";
                analytics.FinalFeedback = completedReview.FinalFeedback ?? string.Empty;
            }

            ViewBag.User = _authService.GetCurrentUser();
            return View(analytics); // Теперь возвращаем GoalAnalyticsResponse
        }
    }
}