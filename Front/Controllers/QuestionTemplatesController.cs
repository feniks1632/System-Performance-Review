using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("question-templates")]
    public class QuestionTemplatesController : Controller
    {
        private readonly IReviewService _reviewService;
        private readonly IAuthService _authService;
        private readonly IApiService _apiService;

        public QuestionTemplatesController(IReviewService reviewService, IAuthService authService, IApiService apiService)
        {
            _reviewService = reviewService ?? throw new ArgumentNullException(nameof(reviewService));
            _authService = authService ?? throw new ArgumentNullException(nameof(authService));
            _apiService = apiService ?? throw new ArgumentNullException(nameof(apiService));
        }

        [HttpGet]
        public async Task<IActionResult> Index(string? question_type = null, string? section = null)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            var templates = await _reviewService.GetQuestionTemplatesAsync(question_type, section);
            
            ViewBag.QuestionType = question_type;
            ViewBag.Section = section;
            
            return View(templates ?? new List<QuestionTemplateResponse>());
        }

        [HttpGet("details/{template_id}")]
        public async Task<IActionResult> Details(string template_id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest("Template ID is required");

            var template = await _apiService.GetAsync<QuestionTemplateResponse>($"question-templates/{template_id}");
            if (template == null)
                return NotFound();

            return View(template);
        }

        [HttpGet("create")]
        public IActionResult Create()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            var model = new QuestionTemplateCreateModel(); // Используем модель для представления
            return View(model);
        }

        [HttpPost("create")]
        public async Task<IActionResult> Create(QuestionTemplateCreateModel createModel) // Изменен тип параметра
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (createModel == null)
            {
                ModelState.AddModelError("", "Request body is required");
                return View(createModel);
            }

            if (!ModelState.IsValid)
            {
                return View(createModel);
            }

            // Преобразуем модель представления в модель запроса API
            var createRequest = new QuestionTemplateCreateRequest
            {
                QuestionText = createModel.QuestionText,
                QuestionType = createModel.QuestionType,
                Section = createModel.Section,
                Weight = createModel.Weight,
                MaxScore = createModel.MaxScore,
                OrderIndex = createModel.OrderIndex,
                TriggerWords = createModel.TriggerWords,
                OptionsJson = createModel.OptionsJson,
                RequiresManagerScoring = createModel.RequiresManagerScoring
            };

            Console.WriteLine("=== DEBUG: Create POST method called ===");
    Console.WriteLine($"Model is null: {createModel == null}");

            if (createModel != null)
            {
                Console.WriteLine($"QuestionText: '{createModel.QuestionText}'");
                Console.WriteLine($"QuestionType: '{createModel.QuestionType}'");
                Console.WriteLine($"Section: '{createModel.Section}'");
                Console.WriteLine($"Weight: {createModel.Weight}");
                Console.WriteLine($"MaxScore: {createModel.MaxScore}");
                Console.WriteLine($"OrderIndex: {createModel.OrderIndex}");
                Console.WriteLine($"TriggerWords: '{createModel.TriggerWords}'");
                Console.WriteLine($"OptionsJson: '{createModel.OptionsJson}'");
                Console.WriteLine($"RequiresManagerScoring: {createModel.RequiresManagerScoring}");
            }

            var template = await _apiService.PostAsync<QuestionTemplateResponse>("question-templates/", createRequest);
            if (template != null)
            {
                TempData["SuccessMessage"] = "Шаблон вопроса успешно создан";
                return RedirectToAction("Index");
            }

            ModelState.AddModelError("", "Ошибка при создании шаблона вопроса");
            return View(createModel);
        }

        [HttpGet("edit/{template_id}")]
        public async Task<IActionResult> Edit(string template_id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest("Template ID is required");

            var template = await _apiService.GetAsync<QuestionTemplateResponse>($"question-templates/{template_id}");
            if (template == null)
                return NotFound();

            var editModel = new QuestionTemplateEditModel
            {
                Id = template.Id,
                QuestionText = template.QuestionText ?? string.Empty,
                QuestionType = template.QuestionType ?? string.Empty,
                Section = template.Section ?? string.Empty,
                Weight = (decimal)template.Weight, // явное преобразование double to decimal
                MaxScore = template.MaxScore,
                OrderIndex = template.OrderIndex,
                TriggerWords = template.TriggerWords ?? string.Empty,
                OptionsJson = template.OptionsJson ?? string.Empty,
                RequiresManagerScoring = template.RequiresManagerScoring
            };

            return View(editModel);
        }

        [HttpPost("edit/{template_id}")]
        public async Task<IActionResult> Edit(string template_id, QuestionTemplateEditModel editModel)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Auth");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest("Template ID is required");

            if (!ModelState.IsValid)
            {
                return View(editModel);
            }

            var updateRequest = new QuestionTemplateUpdateRequest
            {
                QuestionText = editModel.QuestionText,
                QuestionType = editModel.QuestionType,
                Section = editModel.Section,
                Weight = editModel.Weight, // преобразование decimal to double для API
                MaxScore = editModel.MaxScore,
                OrderIndex = editModel.OrderIndex,
                TriggerWords = editModel.TriggerWords,
                OptionsJson = editModel.OptionsJson,
                RequiresManagerScoring = editModel.RequiresManagerScoring
            };

            var template = await _apiService.PutAsync<QuestionTemplateResponse>($"question-templates/{template_id}", updateRequest);
            if (template != null)
            {
                TempData["SuccessMessage"] = "Шаблон вопроса успешно обновлен";
                return RedirectToAction("Index");
            }

            ModelState.AddModelError("", "Ошибка при обновлении шаблона вопроса");
            return View(editModel);
        }

        [HttpPost("delete/{template_id}")]
        public async Task<IActionResult> Delete(string template_id)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Unauthorized" });

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Json(new { success = false, message = "Forbidden" });

            if (string.IsNullOrWhiteSpace(template_id))
                return Json(new { success = false, message = "Template ID is required" });

            var result = await _apiService.DeleteAsync($"question-templates/{template_id}");

            if (result)
            {
                return Json(new { success = true, message = "Шаблон вопроса успешно удален" });
            }

            return Json(new { success = false, message = "Ошибка при удалении шаблона вопроса" });
        }
    }
}