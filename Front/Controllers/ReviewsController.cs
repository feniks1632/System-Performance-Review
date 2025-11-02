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
                createModel.Answers = createModel.Answers?
                    .Where(a => !string.IsNullOrEmpty(a.Answer) || a.Score.HasValue || !string.IsNullOrEmpty(a.SelectedOption))
                    .ToList() ?? new List<AnswerModel>();

                var review = await _reviewService.CreateReviewAsync(createModel);
                if (review != null)
                {
                    if ((createModel.ReviewType == ReviewType.Manager || createModel.ReviewType == ReviewType.Potential) && user?.IsManager == true)
                    {
                        TempData["Success"] = "Оценка создана. Теперь завершите оценку.";
                        return RedirectToAction("CompleteManager", new { id = review.Id });
                    }

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

        [HttpGet("complete-manager/{id}")]
        public async Task<IActionResult> CompleteManager(string id)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
            {
                TempData["Error"] = "Доступ разрешен только руководителям";
                return RedirectToAction("Login", "Home");
            }

            try
            {
                // 1. Получаем только базовую информацию об оценке (БЕЗ ответов сотрудника)
                var review = await _reviewService.GetReviewAsync(id);
                if (review == null)
                {
                    TempData["Error"] = "Оценка не найдена";
                    return RedirectToAction("PendingManagerReviews");
                }

                // 2. Получаем информацию о цели
                var goal = await _apiService.GetAsync<GoalResponse>($"goals/{review.GoalId}");

                // 3. Получаем вопросы ДЛЯ РУКОВОДИТЕЛЯ (без ответов сотрудника!)
                var managerQuestions = await GetManagerQuestionsAsync(review.ReviewType);

                var model = new ManagerScoringViewModel
                {
                    ReviewId = id,
                    Review = review,
                    GoalId = review.GoalId,
                    GoalTitle = goal?.Title ?? "Неизвестная цель",
                    EmployeeName = await GetEmployeeNameAsync(goal),
                    ManagerQuestions = managerQuestions, // Используем ManagerQuestions вместо PendingQuestions
                    ManagerScores = InitializeManagerScores(managerQuestions),
                    FinalReview = new FinalReviewUpdateModel()
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

        private async Task<List<ManagerQuestion>> GetManagerQuestionsAsync(ReviewType reviewType)
        {
            // Получаем вопросы из шаблонов для руководителя
            var questionTemplates = await _reviewService.GetQuestionTemplatesAsync(
                questionType: reviewType.ToString().ToLower(),
                section: "manager" // или другой критерий для вопросов руководителя
            );

            // Если не нашли по section "manager", берем все вопросы для этого типа оценки
            if (!questionTemplates.Any())
            {
                questionTemplates = await _reviewService.GetQuestionTemplatesAsync(
                    questionType: reviewType.ToString().ToLower()
                );
            }

            return questionTemplates.Select(q => new ManagerQuestion
            {
                QuestionId = q.Id,
                QuestionText = q.QuestionText,
                // Используем проверку на 0 или отрицательные значения вместо ??
                MaxScore = q.MaxScore > 0 ? q.MaxScore : 10, // Если MaxScore <= 0, используем 10
                Weight = q.Weight > 0 ? q.Weight : 1.0 // Если Weight <= 0, используем 1.0
            }).ToList();
        }

        // Вспомогательный метод для получения имени сотрудника
        private async Task<string> GetEmployeeNameAsync(GoalResponse? goal)
        {
            if (goal == null) return "Неизвестный сотрудник";

            if (!string.IsNullOrEmpty(goal.EmployeeId))
            {
                try
                {
                    var employee = await _apiService.GetAsync<UserResponse>($"users/{goal.EmployeeId}");
                    return employee?.FullName ?? goal.EmployeeName ?? "Неизвестный сотрудник";
                }
                catch
                {
                    return goal?.EmployeeName ?? "Неизвестный сотрудник";
                }
            }

            return goal?.EmployeeName ?? "Неизвестный сотрудник";
        }

        [HttpPost("complete-manager/{id}")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> CompleteManager(string id, ManagerScoringViewModel model)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
            {
                TempData["Error"] = "Доступ разрешен только руководителям";
                return RedirectToAction("Login", "Home");
            }

            if (!ModelState.IsValid)
            {
                await ReloadManagerScoringModel(id, model);
                ViewBag.User = _authService.GetCurrentUser();
                TempData["Error"] = "Пожалуйста, заполните все обязательные поля";
                return View("CompleteManager", model);
            }

            try
            {
                // 1. Проверяем, что есть оценки для отправки
                var scoresToSave = model.ManagerScores?
                    .Where(score => score.Score.HasValue && !string.IsNullOrEmpty(score.QuestionId))
                    .ToList() ?? new List<AnswerModel>();

                if (!scoresToSave.Any())
                {
                    TempData["Warning"] = "Не выбраны оценки для вопросов";
                    await ReloadManagerScoringModel(id, model);
                    ViewBag.User = _authService.GetCurrentUser();
                    return View("CompleteManager", model);
                }

                // 2. Отправляем оценки через API руководителя
                var scoreResult = await _reviewService.ScoreManagerQuestionsAsync(id, scoresToSave);

                if (scoreResult?.Status != "success")
                {
                    Console.WriteLine($"[ReviewsController] Manager scoring API returned: {scoreResult?.Status} - {scoreResult?.Message}");
                    // Не прерываем процесс, но логируем предупреждение
                    TempData["Warning"] = "Оценки вопросов сохранены с предупреждениями";
                }
                else
                {
                    Console.WriteLine($"[ReviewsController] Manager scores successfully saved for review {id}");
                }

                // 3. Завершаем оценку (финальный рейтинг и обратная связь)
                var finalResult = await _reviewService.UpdateFinalReviewAsync(id, model.FinalReview);

                if (finalResult != null)
                {
                    TempData["Success"] = "Оценка успешно завершена";
                    return RedirectToAction("GoalAnalytics", "Analytics", new { goalId = finalResult.GoalId });
                }
                else
                {
                    await ReloadManagerScoringModel(id, model);
                    ViewBag.User = _authService.GetCurrentUser();
                    TempData["Error"] = "Ошибка при завершении оценки";
                    return View("CompleteManager", model);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error completing review {id}: {ex.Message}");
                await ReloadManagerScoringModel(id, model);
                ViewBag.User = _authService.GetCurrentUser();
                TempData["Error"] = $"Ошибка при завершении оценки: {ex.Message}";
                return View("CompleteManager", model);
            }
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

        private async Task ReloadManagerScoringModel(string id, ManagerScoringViewModel model)
        {
            try
            {
                // Используем GetReviewAsync вместо GetReviewWithAnswersAsync
                var review = await _reviewService.GetReviewAsync(id);
                if (review == null) return;

                model.Review = review;
                model.GoalId = review.GoalId;

                var goal = await _apiService.GetAsync<GoalResponse>($"goals/{review.GoalId}");
                model.GoalTitle = goal?.Title ?? "Неизвестная цель";

                string employeeName = "Неизвестный сотрудник";
                if (!string.IsNullOrEmpty(goal?.EmployeeId))
                {
                    try
                    {
                        var employee = await _apiService.GetAsync<UserResponse>($"users/{goal.EmployeeId}");
                        employeeName = employee?.FullName ?? goal.EmployeeName ?? "Неизвестный сотрудник";
                    }
                    catch
                    {
                        employeeName = goal?.EmployeeName ?? "Неизвестный сотрудник";
                    }
                }
                model.EmployeeName = employeeName;

                // Получаем вопросы руководителя заново
                var managerQuestions = await GetManagerQuestionsAsync(review.ReviewType);
                model.ManagerQuestions = managerQuestions;

                if (model.ManagerScores == null || !model.ManagerScores.Any())
                {
                    model.ManagerScores = InitializeManagerScores(managerQuestions);
                }

                if (model.FinalReview == null)
                {
                    model.FinalReview = new FinalReviewUpdateModel();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ReviewsController] Error reloading model: {ex.Message}");
            }
        }

        private List<PendingQuestion> ExtractPendingQuestionsFromReview(ReviewResponseWithAnswers review)
        {
            var questions = new List<PendingQuestion>();

            List<Dictionary<string, object>>? answers = review.ReviewType switch
            {
                ReviewType.Manager => review.ManagerEvaluationAnswers,
                ReviewType.Potential => review.PotentialEvaluationAnswers,
                _ => null
            };

            if (answers == null) return questions;

            foreach (var answer in answers)
            {
                var question = new PendingQuestion();

                if (answer.TryGetValue("question_id", out var questionId))
                    question.QuestionId = questionId?.ToString() ?? string.Empty;

                if (answer.TryGetValue("question_text", out var questionText))
                    question.QuestionText = questionText?.ToString() ?? "Неизвестный вопрос";

                if (answer.TryGetValue("answer", out var answerText))
                    question.Answer = answerText?.ToString();

                if (answer.TryGetValue("score", out var scoreObj) && scoreObj != null)
                {
                    if (double.TryParse(scoreObj.ToString(), out double score))
                        question.CurrentScore = score;
                }

                if (answer.TryGetValue("weight", out var weightObj) && weightObj != null)
                {
                    if (double.TryParse(weightObj.ToString(), out double weight))
                        question.Weight = weight;
                }
                else
                {
                    question.Weight = 1.0;
                }

                if (answer.TryGetValue("max_score", out var maxScoreObj) && maxScoreObj != null)
                {
                    if (int.TryParse(maxScoreObj.ToString(), out int maxScore))
                        question.MaxScore = maxScore;
                }
                else
                {
                    question.MaxScore = 10;
                }

                if (answer.TryGetValue("section", out var section))
                    question.Section = section?.ToString();

                questions.Add(question);
            }

            return questions;
        }

        private List<AnswerModel> InitializeManagerScores(List<ManagerQuestion> managerQuestions)
        {
            return managerQuestions.Select(q => new AnswerModel
            {
                QuestionId = q.QuestionId,
                Score = null,
                Answer = null,
                SelectedOption = null
            }).ToList();
        }
    }
}