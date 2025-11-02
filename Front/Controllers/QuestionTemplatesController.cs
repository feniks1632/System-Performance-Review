using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [ApiController]
    [Route("question-templates")]
    public class QuestionTemplatesController : ControllerBase
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
        public async Task<ActionResult<List<QuestionTemplateResponse>>> GetQuestionTemplates(
            [FromQuery] string? question_type = null,
            [FromQuery] string? section = null)
        {
            if (!_authService.IsAuthenticated())
                return Unauthorized();

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            var templates = await _reviewService.GetQuestionTemplatesAsync(question_type, section);
            return Ok(templates ?? new List<QuestionTemplateResponse>());
        }

        [HttpGet("{template_id}")]
        public async Task<ActionResult<QuestionTemplateResponse>> GetQuestionTemplateById(string template_id)
        {
            if (!_authService.IsAuthenticated())
                return Unauthorized();

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest(new { message = "Template ID is required" });

            var template = await _apiService.GetAsync<QuestionTemplateResponse>($"question-templates/{template_id}");
            if (template == null)
                return NotFound();

            return Ok(template);
        }

        [HttpPost]
        public async Task<ActionResult<QuestionTemplateResponse>> CreateQuestionTemplate(QuestionTemplateCreateRequest createRequest)
        {
            if (!_authService.IsAuthenticated())
                return Unauthorized();

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (createRequest == null)
                return BadRequest(new { message = "Request body is required" });

            if (!ModelState.IsValid)
            {
                var errors = ModelState
                    .Where(x => x.Value != null && x.Value.Errors != null && x.Value.Errors.Count > 0)
                    .Select(x => new ValidationErrorDetail
                    {
                        Loc = new[] { x.Key },
                        Msg = string.Join(", ", x.Value!.Errors
                            .Where(e => !string.IsNullOrEmpty(e.ErrorMessage))
                            .Select(e => e.ErrorMessage!)),
                        Type = "value_error"
                    })
                    .ToArray();

                return BadRequest(new ValidationErrorResponse
                {
                    Detail = errors
                });
            }

            var template = await _apiService.PostAsync<QuestionTemplateResponse>("question-templates", createRequest);
            if (template != null)
            {
                return Ok(template);
            }

            return BadRequest(new { message = "Ошибка при создании шаблона вопроса" });
        }

        [HttpPut("{template_id}")]
        public async Task<ActionResult<QuestionTemplateResponse>> UpdateQuestionTemplate(string template_id, QuestionTemplateUpdateRequest updateRequest)
        {
            if (!_authService.IsAuthenticated())
                return Unauthorized();

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest(new { message = "Template ID is required" });

            if (updateRequest == null)
                return BadRequest(new { message = "Request body is required" });

            if (!ModelState.IsValid)
            {
                var errors = ModelState
                    .Where(x => x.Value != null && x.Value.Errors != null && x.Value.Errors.Count > 0)
                    .Select(x => new ValidationErrorDetail
                    {
                        Loc = new[] { x.Key },
                        Msg = string.Join(", ", x.Value!.Errors
                            .Where(e => !string.IsNullOrEmpty(e.ErrorMessage))
                            .Select(e => e.ErrorMessage!)),
                        Type = "value_error"
                    })
                    .ToArray();

                return BadRequest(new ValidationErrorResponse
                {
                    Detail = errors
                });
            }

            var template = await _apiService.PutAsync<QuestionTemplateResponse>($"question-templates/{template_id}", updateRequest);
            if (template != null)
            {
                return Ok(template);
            }

            return BadRequest(new { message = "Ошибка при обновлении шаблона вопроса" });
        }

        [HttpDelete("{template_id}")]
        public async Task<ActionResult<StatusResponse>> DeleteQuestionTemplate(string template_id)
        {
            if (!_authService.IsAuthenticated())
                return Unauthorized();

            var currentUser = _authService.GetCurrentUser();
            if (currentUser?.IsManager != true)
                return Forbid();

            if (string.IsNullOrWhiteSpace(template_id))
                return BadRequest(new { message = "Template ID is required" });

            var result = await _apiService.DeleteAsync($"question-templates/{template_id}");

            if (result)
            {
                return Ok(new StatusResponse
                {
                    Status = "success",
                    Message = "Шаблон вопроса успешно удален"
                });
            }

            return BadRequest(new StatusResponse
            {
                Status = "error",
                Message = "Ошибка при удалении шаблона вопроса"
            });
        }
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