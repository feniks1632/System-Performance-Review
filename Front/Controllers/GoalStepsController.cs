// Controllers/GoalStepsController.cs

using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("goal-steps")]
    public class GoalStepController : Controller
    {
        private readonly IGoalStepService _goalStepService;
        private readonly IAuthService _authService;

        public GoalStepController(IGoalStepService goalStepService, IAuthService authService)
        {
            _goalStepService = goalStepService;
            _authService = authService;
        }

        [HttpPost("create/{goalId}")]
        public async Task<IActionResult> Create(string goalId, GoalStepCreateModel createModel)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var step = await _goalStepService.CreateGoalStepAsync(goalId, createModel);
            return Json(new { success = step != null, data = step });
        }

        [HttpPost("update/{stepId}")]
        public async Task<IActionResult> Update(string stepId, GoalStepUpdateModel updateModel)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var step = await _goalStepService.UpdateGoalStepAsync(stepId, updateModel);
            return Json(new { success = step != null, data = step });
        }

        [HttpPost("delete/{stepId}")]
        public async Task<IActionResult> Delete(string stepId)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var success = await _goalStepService.DeleteGoalStepAsync(stepId);
            return Json(new { success, message = success ? "Подпункт удален" : "Ошибка удаления" });
        }

        [HttpPost("complete/{stepId}")]
        public async Task<IActionResult> Complete(string stepId)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var step = await _goalStepService.CompleteGoalStepAsync(stepId);
            return Json(new { success = step != null, data = step });
        }

        [HttpPost("incomplete/{stepId}")]
        public async Task<IActionResult> Incomplete(string stepId)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var step = await _goalStepService.IncompleteGoalStepAsync(stepId);
            return Json(new { success = step != null, data = step });
        }
    }
}