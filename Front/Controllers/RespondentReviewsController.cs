// Controllers/RespondentReviewsController.cs

using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("respondent-reviews")]
    public class RespondentReviewsController : Controller
    {
        private readonly IReviewService _reviewService;
        private readonly IApiService _apiService;
        private readonly IAuthService _authService;

        public RespondentReviewsController(IReviewService reviewService, IApiService apiService, IAuthService authService)
        {
            _reviewService = reviewService;
            _apiService = apiService;
            _authService = authService;
        }

        [HttpGet("create/{goalId}")]
        public async Task<IActionResult> Create(string goalId)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var goal = await _apiService.GetAsync<GoalResponse>($"goals/respondent/{goalId}");
            if (goal == null)
            {
                TempData["Error"] = "Вы не являетесь респондентом этой цели или цель не найдена";
                return RedirectToAction("RespondentGoals", "Goals");
            }

            var questions = await _reviewService.GetQuestionTemplatesAsync("respondent");

            // ДИАГНОСТИКА
            Console.WriteLine("=== RESPONDENT REVIEW DEBUG ===");
            Console.WriteLine($"Goal: {goal.Title} (ID: {goal.Id})");
            Console.WriteLine($"Questions count: {questions?.Count ?? 0}");

            if (questions != null)
            {
                foreach (var question in questions)
                {
                    Console.WriteLine($"Question: {question.QuestionText}");
                    Console.WriteLine($"Type: '{question.QuestionType}'");
                    Console.WriteLine($"Normalized: '{question.QuestionType?.ToLowerInvariant()?.Trim()}'");
                    Console.WriteLine($"Is 'respondent': {question.QuestionType?.ToLowerInvariant()?.Trim() == "respondent"}");
                    Console.WriteLine("---");
                }
            }
            Console.WriteLine("=== END DEBUG ===");

            var model = new RespondentReviewViewModel
            {
                GoalId = goalId,
                GoalTitle = goal.Title,
                Questions = questions ?? new List<QuestionTemplateResponse>()
            };

            ViewBag.User = _authService.GetCurrentUser();
            return View(model);
        }

        [HttpPost("create")]
        public async Task<IActionResult> Create(RespondentReviewCreateModel createModel)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            if (!ModelState.IsValid)
            {
                // ПЕРЕСОЗДАЕМ ViewModel для возврата в View
                var goal = await _apiService.GetAsync<GoalResponse>($"goals/respondent/{createModel.GoalId}");
                var questions = await _reviewService.GetQuestionTemplatesAsync("respondent");

                var viewModel = new RespondentReviewViewModel
                {
                    GoalId = createModel.GoalId,
                    GoalTitle = goal?.Title ?? "Неизвестная цель",
                    Questions = questions ?? new List<QuestionTemplateResponse>(),
                    Review = createModel
                };

                ViewBag.User = _authService.GetCurrentUser();
                return View(viewModel);
            }

            var review = await _reviewService.CreateRespondentReviewAsync(createModel);
            if (review != null)
            {
                TempData["Success"] = "Оценка успешно отправлена";
                return RedirectToAction("RespondentGoals", "Goals");
            }

            // ТАКЖЕ ИСПРАВИТЕ ЗДЕСЬ ПРИ ОШИБКЕ
            var errorGoal = await _apiService.GetAsync<GoalResponse>($"goals/respondent/{createModel.GoalId}");
            var errorQuestions = await _reviewService.GetQuestionTemplatesAsync("respondent");

            var errorViewModel = new RespondentReviewViewModel
            {
                GoalId = createModel.GoalId,
                GoalTitle = errorGoal?.Title ?? "Неизвестная цель",
                Questions = errorQuestions ?? new List<QuestionTemplateResponse>(),
                Review = createModel
            };

            ModelState.AddModelError("", "Ошибка при создании оценки");
            ViewBag.User = _authService.GetCurrentUser();
            return View(errorViewModel);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> Details(string id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var review = await _reviewService.GetRespondentReviewAsync(id);
            if (review == null)
                return NotFound();

            ViewBag.User = _authService.GetCurrentUser();
            return View(review);
        }
    }
    
    public class RespondentReviewViewModel
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public List<QuestionTemplateResponse> Questions { get; set; } = new List<QuestionTemplateResponse>();
        public RespondentReviewCreateModel Review { get; set; } = new RespondentReviewCreateModel();
    }
}