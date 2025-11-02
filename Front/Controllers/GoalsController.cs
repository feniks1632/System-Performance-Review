// Controllers/GoalsController.cs

using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("goals")]
    public class GoalsController : Controller
    {
        private readonly IApiService _apiService;
        private readonly IAuthService _authService;
        private readonly IUserService _userService;

        public GoalsController(IApiService apiService, IAuthService authService, IUserService userService)
        {
            _apiService = apiService;
            _authService = authService;
            _userService = userService;
        }

        public async Task<IActionResult> Index()
        {
            if (!_authService.IsAuthenticated())
            {
                return RedirectToAction("Login", "Home");
            }

            var user = _authService.GetCurrentUser();
            var goals = await _apiService.GetAsync<List<GoalResponse>>($"goals/employee/{user?.Id}");

            ViewBag.User = user;
            return View(goals ?? new List<GoalResponse>());
        }

        [HttpGet("create")]
        public IActionResult Create()
        {
            if (!_authService.IsAuthenticated())
            {
                return RedirectToAction("Login", "Home");
            }

            var user = _authService.GetCurrentUser();
            ViewBag.User = user;

            var model = new GoalCreateModel();

            return View(model);
        }

        [HttpPost("create")]
        public async Task<IActionResult> Create(GoalCreateModel createModel)
        {
            Console.WriteLine("=== НАЧАЛО СОЗДАНИЯ ЦЕЛИ ===");

            if (!_authService.IsAuthenticated())
            {
                Console.WriteLine("Пользователь не аутентифицирован");
                return RedirectToAction("Login", "Home");
            }

            var currentUser = _authService.GetCurrentUser();
            Console.WriteLine($"Текущий пользователь: {currentUser?.FullName} ({currentUser?.Id})");

            // ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ ТОКЕНА
            var token = _authService.GetToken();
            if (!string.IsNullOrEmpty(token))
            {
                _apiService.SetToken(token);
                Console.WriteLine($"Токен принудительно установлен в ApiService");
            }

            if (!ModelState.IsValid)
            {
                Console.WriteLine("Модель не валидна:");
                foreach (var error in ModelState.Values.SelectMany(v => v.Errors))
                {
                    Console.WriteLine($" - {error.ErrorMessage}");
                }
                ViewBag.User = currentUser;
                return View(createModel);
            }

            try
            {
                var stepsList = new List<object>();

                if (createModel.Steps != null)
                {
                    foreach (var step in createModel.Steps)
                    {
                        if (step != null && !string.IsNullOrEmpty(step.Title))
                        {
                            stepsList.Add(new
                            {
                                title = step.Title,
                                description = step.Description ?? string.Empty,
                                order_index = step.OrderIndex
                            });
                        }
                    }
                }

                var goalRequest = new
                {
                    title = createModel.Title,
                    description = createModel.Description,
                    expected_result = createModel.ExpectedResult,
                    deadline = createModel.Deadline.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                    task_link = createModel.TaskLink ?? string.Empty,
                    respondent_ids = createModel.RespondentIdsList,
                    steps = stepsList
                };

                Console.WriteLine($"Отправка запроса создания цели...");

                // СОЗДАЕМ ЦЕЛЬ
                var goal = await _apiService.PostAsync<GoalResponse>("goals/", goalRequest, suppressAuthClear: true);

                if (goal != null)
                {

                    TempData["Success"] = "Цель успешно создана";
                    return RedirectToAction("Index");
                }
                else
                {
                    Console.WriteLine("Ошибка: API вернул null при создании цели");
                    ModelState.AddModelError("", "Не удалось создать цель. Проверьте введенные данные и права доступа.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Исключение при создании цели: {ex.Message}");
                Console.WriteLine($"Stack trace: {ex.StackTrace}");
                ModelState.AddModelError("", $"Ошибка при создании цели: {ex.Message}");
            }

            ViewBag.User = currentUser;
            return View(createModel);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> Details(string id)
        {
            if (!_authService.IsAuthenticated())
            {
                return RedirectToAction("Login", "Home");
            }

            var goal = await _apiService.GetAsync<GoalResponse>($"goals/{id}");
            if (goal == null)
            {
                return NotFound();
            }

            ViewBag.User = _authService.GetCurrentUser();
            return View(goal);
        }

        [HttpGet("respondent")]
        public async Task<IActionResult> RespondentGoals()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var goals = await _apiService.GetAsync<List<GoalResponse>>("goals/respondent/my");

            ViewBag.User = _authService.GetCurrentUser();
            return View(goals ?? new List<GoalResponse>());
        }

        [HttpGet("respondent/{goalId}")]
        public async Task<IActionResult> RespondentGoalDetails(string goalId)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            Console.WriteLine($"[GoalsController] Получение цели респондента: {goalId}");

            // Используем endpoint для получения конкретной цели респондента
            var goal = await _apiService.GetAsync<GoalResponse>($"goals/respondent/{goalId}");

            if (goal == null)
            {
                Console.WriteLine($"[GoalsController] Цель респондента {goalId} не найдена");
                return NotFound();
            }

            Console.WriteLine($"[GoalsController] Найдена цель респондента: {goal.Title}");

            ViewBag.User = _authService.GetCurrentUser();
            return View("RespondentGoalDetails", goal);
        }

        [HttpPost("{goalId}/complete")]
        public async Task<IActionResult> CompleteGoal(string goalId)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var result = await _apiService.PutAsync<SuccessResponse>($"goals/{goalId}/status", new { status = "completed" });
            return Json(new { success = result != null, message = result?.Message });
        }

        [HttpPost("{goalId}/cancel")]
        public async Task<IActionResult> CancelGoal(string goalId)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var result = await _apiService.PutAsync<SuccessResponse>($"goals/{goalId}/status", new { status = "cancelled" });
            return Json(new { success = result != null, message = result?.Message });
        }
    }
}