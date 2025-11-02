using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("reviews")]
    public class ReviewsController : Controller
    {
        private readonly IReviewService _reviewService;
        private readonly IApiService _apiService;
        private readonly IAuthService _authService;

        public ReviewsController(IReviewService reviewService, IApiService apiService, IAuthService authService)
        {
            _reviewService = reviewService;
            _apiService = apiService;
            _authService = authService;
        }

        [HttpGet("create/{goalId}/{reviewType}")]
        public async Task<IActionResult> Create(string goalId, string reviewType)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var goal = await _apiService.GetAsync<GoalResponse>($"goals/{goalId}");
            if (goal == null)
            {
                TempData["Error"] = "Цель не найдена";
                return RedirectToAction("Index", "Goals");
            }

            var user = _authService.GetCurrentUser();

            // ПРОВЕРКА ПРАВ ДОСТУПА ДЛЯ ОЦЕНКИ ПОТЕНЦИАЛА
            if (reviewType.ToLower() == "potential" && user?.IsManager != true)
            {
                TempData["Error"] = "Оценка потенциала доступна только руководителям";
                return RedirectToAction("Details", "Goals", new { id = goalId });
            }

            if (reviewType.ToLower() == "self" && goal.EmployeeId != user?.Id)
            {
                TempData["Error"] = "Вы можете создавать самооценку только для своих целей";
                return RedirectToAction("Details", "Goals", new { id = goalId });
            }

            // Исправлено: правильное преобразование типа оценки
            if (!Enum.TryParse<ReviewType>(reviewType, true, out var reviewTypeEnum))
            {
                TempData["Error"] = "Неверный тип оценки";
                return RedirectToAction("Details", "Goals", new { id = goalId });
            }

            var questions = await _reviewService.GetQuestionTemplatesAsync(reviewType.ToLower());

            var model = new ReviewCreateViewModel
            {
                GoalId = goalId,
                GoalTitle = goal.Title,
                ReviewType = reviewTypeEnum,
                Questions = questions ?? new List<QuestionTemplateResponse>(),
                Review = new ReviewCreateModel
                {
                    GoalId = goalId,
                    ReviewType = reviewTypeEnum,
                    Answers = questions?.Select(q => new AnswerModel
                    {
                        QuestionId = q.Id
                    }).ToList() ?? new List<AnswerModel>()
                }
            };

            ViewBag.User = user;
            return View(model);
        }

        [HttpGet("completed")]
        public async Task<IActionResult> CompletedReviews()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var user = _authService.GetCurrentUser();
            var reviews = await _reviewService.GetReviewsAsync();

            // Для сотрудника: показываем завершенные оценки его целей
            // Для руководителя: показываем все завершенные оценки
            var completedReviews = reviews?
                .Where(r => !string.IsNullOrEmpty(r.FinalRating) &&
                           (user?.IsManager == true || r.ReviewerId == user?.Id))
                .ToList() ?? new List<ReviewResponse>();

            ViewBag.User = user;
            return View(completedReviews);
        }

        [HttpPost("create")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create(ReviewCreateModel createModel)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var user = _authService.GetCurrentUser();
            var goal = await _apiService.GetAsync<GoalResponse>($"goals/{createModel.GoalId}");

            if (!ModelState.IsValid || goal == null)
            {
                var questions = await _reviewService.GetQuestionTemplatesAsync(createModel.ReviewType.ToString().ToLower());

                var viewModel = new ReviewCreateViewModel
                {
                    GoalId = createModel.GoalId,
                    GoalTitle = goal?.Title ?? "Неизвестная цель",
                    ReviewType = createModel.ReviewType,
                    Questions = questions ?? new List<QuestionTemplateResponse>(),
                    Review = createModel
                };

                ViewBag.User = user;
                TempData["Error"] = "Пожалуйста, проверьте введенные данные";
                return View(viewModel);
            }

            try
            {
                // Фильтруем пустые ответы
                createModel.Answers = createModel.Answers?
                    .Where(a => !string.IsNullOrEmpty(a.Answer) || a.Score.HasValue || !string.IsNullOrEmpty(a.SelectedOption))
                    .ToList() ?? new List<AnswerModel>();

                var review = await _reviewService.CreateReviewAsync(createModel);
                if (review != null)
                {
                    // Если это оценка руководителя или потенциала - перенаправляем на завершение
                    if ((createModel.ReviewType == ReviewType.Manager || createModel.ReviewType == ReviewType.Potential) && user?.IsManager == true)
                    {
                        TempData["Success"] = "Оценка создана. Теперь завершите её.";
                        return RedirectToAction("CompleteManagerReview", new { id = review.Id });
                    }

                    // Для самооценки - показываем аналитику
                    if (createModel.ReviewType == ReviewType.Self)
                    {
                        TempData["Success"] = "Самооценка успешно создана";
                        return RedirectToAction("GoalAnalytics", "Analytics", new { goalId = createModel.GoalId });
                    }

                    TempData["Success"] = "Оценка успешно создана";
                    return RedirectToAction("Details", "Goals", new { id = createModel.GoalId });
                }

                TempData["Error"] = "Ошибка при создании оценки";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error creating review: {ex.Message}");
                TempData["Error"] = "Произошла ошибка при создании оценки";
            }

            // Возврат с ошибкой
            var errorQuestions = await _reviewService.GetQuestionTemplatesAsync(createModel.ReviewType.ToString().ToLower());
            var errorViewModel = new ReviewCreateViewModel
            {
                GoalId = createModel.GoalId,
                GoalTitle = goal.Title,
                ReviewType = createModel.ReviewType,
                Questions = errorQuestions ?? new List<QuestionTemplateResponse>(),
                Review = createModel
            };

            ViewBag.User = user;
            return View(errorViewModel);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> Details(string id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var review = await _reviewService.GetReviewWithAnswersAsync(id);
            if (review == null)
            {
                TempData["Error"] = "Оценка не найдена";
                return RedirectToAction("Index", "Goals");
            }

            ViewBag.User = _authService.GetCurrentUser();
            return View(review);
        }

        [HttpPost("{id}/final")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> FinalizeReview(string id, FinalReviewUpdateModel updateModel)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var user = _authService.GetCurrentUser();
            if (user?.IsManager != true)
                return Json(new { success = false, message = "Только руководители могут завершать оценки" });

            var result = await _reviewService.UpdateFinalReviewAsync(id, updateModel);
            return Json(new { 
                success = result != null, 
                message = result != null ? "Оценка завершена" : "Ошибка при завершении оценки" 
            });
        }

        [HttpGet("{id}/pending-manager-scores")]
        public async Task<IActionResult> PendingManagerScores(string id)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
                return Json(new { success = false, message = "Не авторизован" });

            var pendingScores = await _reviewService.GetPendingManagerScoresAsync(id);
            return Json(new { success = true, data = pendingScores });
        }

        [HttpGet("pending-manager")]
        public async Task<IActionResult> PendingManagerReviews()
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
            {
                TempData["Error"] = "Доступ разрешен только руководителям";
                return RedirectToAction("Login", "Home");
            }

            try
            {
                var pendingReviews = await _reviewService.GetPendingManagerReviewsAsync();
                ViewBag.User = _authService.GetCurrentUser();
                return View(pendingReviews ?? new List<ReviewResponse>());
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error getting pending manager reviews: {ex.Message}");
                TempData["Error"] = "Ошибка при загрузке оценок";
                return View(new List<ReviewResponse>());
            }
        }

        [HttpGet("complete-manager/{id}")]
        public async Task<IActionResult> CompleteManagerReview(string id)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
            {
                TempData["Error"] = "Доступ разрешен только руководителям";
                return RedirectToAction("Login", "Home");
            }

            try
            {
                var review = await _reviewService.GetReviewAsync(id);
                if (review == null)
                {
                    TempData["Error"] = "Оценка не найдена";
                    return RedirectToAction("PendingManagerReviews");
                }

                var pendingQuestionsData = await _reviewService.GetPendingManagerScoresAsync(id);
                var pendingQuestions = ParsePendingQuestions(pendingQuestionsData);

                var model = new ManagerScoringViewModel
                {
                    ReviewId = id,
                    Review = review,
                    PendingQuestions = pendingQuestions,
                    FinalReview = new FinalReviewUpdateModel(),
                    ManagerScores = InitializeManagerScores(pendingQuestions)
                };

                ViewBag.User = _authService.GetCurrentUser();
                return View(model);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error loading review {id}: {ex.Message}");
                TempData["Error"] = "Ошибка при загрузке оценки";
                return RedirectToAction("PendingManagerReviews");
            }
        }

        [HttpPost("complete-manager/{id}")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> CompleteManagerReview(string id, ManagerScoringViewModel model)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
            {
                TempData["Error"] = "Доступ разрешен только руководителям";
                return RedirectToAction("Login", "Home");
            }

            if (!ModelState.IsValid)
            {
                // Перезагружаем данные для формы
                var review = await _reviewService.GetReviewAsync(id);
                var pendingQuestionsData = await _reviewService.GetPendingManagerScoresAsync(id);
                var pendingQuestions = ParsePendingQuestions(pendingQuestionsData);

                model.Review = review;
                model.PendingQuestions = pendingQuestions;
                model.ManagerScores = InitializeManagerScores(pendingQuestions);

                ViewBag.User = _authService.GetCurrentUser();
                TempData["Error"] = "Пожалуйста, заполните все обязательные поля";
                return View(model);
            }

            try
            {
                // Сохраняем оценки руководителя
                var scoresToSave = model.ManagerScores?
                    .Where(score => score.Score.HasValue && !string.IsNullOrEmpty(score.QuestionId))
                    .ToList() ?? new List<AnswerModel>();

                if (scoresToSave.Any())
                {
                    var scoreResult = await _reviewService.ScoreManagerQuestionsAsync(id, scoresToSave);
                    if (scoreResult == null)
                    {
                        TempData["Warning"] = "Оценки не были сохранены";
                    }
                }

                // Завершаем оценку через API
                var result = await _reviewService.UpdateFinalReviewAsync(id, model.FinalReview);

                if (result != null)
                {
                    TempData["Success"] = "Оценка успешно завершена";

                    // Перенаправляем на аналитику цели
                    return RedirectToAction("GoalAnalytics", "Analytics", new { goalId = result.GoalId });
                }
                else
                {
                    TempData["Error"] = "Ошибка при завершении оценки";
                    return RedirectToAction("CompleteManagerReview", new { id });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error completing review {id}: {ex.Message}");
                TempData["Error"] = $"Ошибка при завершении оценки: {ex.Message}";
                return RedirectToAction("CompleteManagerReview", new { id });
            }
        }

        [HttpPost("{id}/score-manager-questions")]
        public async Task<IActionResult> ScoreManagerQuestions(string id, List<ManagerScoreRequest> scores)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
                return Json(new { success = false, message = "Не авторизован" });

            try
            {
                var answerModels = scores.Select(score => new AnswerModel
                {
                    QuestionId = score.QuestionId,
                    Score = score.Score,
                    Answer = score.Feedback
                }).ToList();

                var result = await _reviewService.ScoreManagerQuestionsAsync(id, answerModels);
                return Json(new { 
                    success = result != null, 
                    message = result != null ? "Оценки сохранены" : "Ошибка при сохранении оценок" 
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error scoring questions for {id}: {ex.Message}");
                return Json(new { success = false, message = $"Ошибка: {ex.Message}" });
            }
        }

        [HttpGet("self-assessments")]
        public async Task<IActionResult> SelfAssessments()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var currentUser = _authService.GetCurrentUser();
            var reviews = await _reviewService.GetReviewsAsync();

            var selfAssessments = reviews?
                .Where(r => r.ReviewerId == currentUser?.Id && r.ReviewType == ReviewType.Self)
                .ToList() ?? new List<ReviewResponse>();

            ViewBag.User = currentUser;
            return View(selfAssessments);
        }

        private List<PendingQuestion> ParsePendingQuestions(List<Dictionary<string, object>>? pendingData)
        {
            var questions = new List<PendingQuestion>();

            if (pendingData == null) return questions;

            foreach (var item in pendingData)
            {
                var question = new PendingQuestion();
                
                if (item.TryGetValue("question_id", out var questionId))
                    question.QuestionId = questionId?.ToString() ?? string.Empty;
                
                if (item.TryGetValue("question_text", out var questionText))
                    question.QuestionText = questionText?.ToString() ?? "Неизвестный вопрос";
                
                if (item.TryGetValue("answer", out var answer))
                    question.Answer = answer?.ToString();
                
                if (item.TryGetValue("current_score", out var currentScore) && currentScore != null)
                {
                    if (double.TryParse(currentScore.ToString(), out double score))
                        question.CurrentScore = score;
                }
                
                if (item.TryGetValue("question_type", out var questionType))
                    question.QuestionType = questionType?.ToString();
                
                if (item.TryGetValue("weight", out var weight) && weight != null)
                {
                    if (double.TryParse(weight.ToString(), out double weightValue))
                        question.Weight = weightValue;
                }
                
                if (item.TryGetValue("max_score", out var maxScore) && maxScore != null)
                {
                    if (int.TryParse(maxScore.ToString(), out int maxScoreValue))
                        question.MaxScore = maxScoreValue;
                }
                
                if (item.TryGetValue("section", out var section))
                    question.Section = section?.ToString();

                questions.Add(question);
            }

            return questions;
        }

        private List<AnswerModel> InitializeManagerScores(List<PendingQuestion> pendingQuestions)
        {
            return pendingQuestions.Select(q => new AnswerModel
            {
                QuestionId = q.QuestionId,
                Score = null,
                Answer = null
            }).ToList();
        }
    }
}