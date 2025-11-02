// Controllers/UsersController.cs

using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    [Route("users")]
    public class UsersController : Controller
    {
        private readonly IUserService _userService;
        private readonly IAuthService _authService;

        public UsersController(IUserService userService, IAuthService authService)
        {
            _userService = userService;
            _authService = authService;
        }

        [HttpGet("profile")]
        public async Task<IActionResult> Profile()
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser == null)
                return RedirectToAction("Login", "Home");

            return await BuildProfileViewModel(currentUser);
        }

        [HttpGet("profile/{id}")]
        public async Task<IActionResult> ProfileById(string id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var currentUser = _authService.GetCurrentUser();
            if (currentUser == null)
                return RedirectToAction("Login", "Home");

            // Users can view their own profile, managers can view any profile
            if (currentUser.Id != id && currentUser.IsManager != true)
                return Forbid();

            UserResponse? user;
            if (currentUser.Id == id)
            {
                user = currentUser;
            }
            else
            {
                user = await _userService.GetUserByIdAsync(id);
                if (user == null)
                    return NotFound();
            }

            return await BuildProfileViewModel(user);
        }

        [HttpGet("managers")]
        public async Task<IActionResult> Managers()
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
                return RedirectToAction("Login", "Home");

            var managers = await _userService.GetManagersAsync();
            ViewBag.User = _authService.GetCurrentUser();
            return View(managers);
        }

        [HttpGet("subordinates")]
        public async Task<IActionResult> Subordinates()
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
                return RedirectToAction("Login", "Home");

            var subordinates = await _userService.GetMySubordinatesAsync();
            ViewBag.User = _authService.GetCurrentUser();
            return View(subordinates);
        }

        [HttpPost("check-user")]
        public async Task<IActionResult> CheckUser([FromBody] AssignManagerModel model)
        {
            if (!_authService.IsAuthenticated() || _authService.GetCurrentUser()?.IsManager != true)
                return Json(new { success = false, message = "Недостаточно прав" });

            try
            {
                var user = await _userService.GetUserByIdAsync(model.UserId);
                if (user == null)
                {
                    return Json(new
                    {
                        success = false,
                        message = "Пользователь с таким ID не найден"
                    });
                }

                return Json(new
                {
                    success = true,
                    user = new
                    {
                        user.Id,
                        user.FullName,
                        user.Email,
                        user.IsManager,
                        user.IsActive
                    }
                });
            }
            catch (Exception ex)
            {
                return Json(new
                {
                    success = false,
                    message = $"Ошибка при проверке пользователя: {ex.Message}"
                });
            }
        }

        [HttpPost("assign-manager")]
        public async Task<IActionResult> AssignManager([FromBody] AssignManagerModel model)
        {
            if (!_authService.IsAuthenticated())
                return Json(new { success = false, message = "Не авторизован" });

            var currentUser = _authService.GetCurrentUser();

            // Проверяем что текущий пользователь - руководитель и это его ID
            if (currentUser?.IsManager != true)
                return Json(new { success = false, message = "Недостаточно прав. Только руководители могут назначать руководителей." });

            if (currentUser.Id != model.ManagerId)
                return Json(new { success = false, message = "Вы можете назначить только себя руководителем" });

            try
            {
                // Проверяем что пользователь существует
                var targetUser = await _userService.GetUserByIdAsync(model.UserId);
                if (targetUser == null)
                {
                    return Json(new
                    {
                        success = false,
                        message = "Пользователь с таким ID не найден"
                    });
                }

                // Проверяем что не назначаем себя себе
                if (targetUser.Id == model.ManagerId)
                {
                    return Json(new
                    {
                        success = false,
                        message = "Нельзя назначить себя себе руководителем"
                    });
                }

                // Используем переданные user_id и manager_id
                var success = await _userService.AssignManagerAsync(model.UserId, model.ManagerId);

                if (success)
                {
                    return Json(new
                    {
                        success = true,
                        message = $"Вы успешно назначены руководителем для {targetUser.FullName}",
                        userName = targetUser.FullName
                    });
                }
                else
                {
                    return Json(new
                    {
                        success = false,
                        message = "Ошибка при назначении руководителя"
                    });
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error assigning manager: {ex.Message}");
                return Json(new
                {
                    success = false,
                    message = "Произошла ошибка при выполнении запроса"
                });
            }
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> Details(string id)
        {
            if (!_authService.IsAuthenticated())
                return RedirectToAction("Login", "Home");

            var currentUser = _authService.GetCurrentUser();

            if (currentUser?.IsManager != true && currentUser?.Id != id)
                return Forbid();

            var user = await _userService.GetUserByIdAsync(id);
            if (user == null)
                return NotFound();

            ViewBag.User = currentUser;
            return View(user);
        }

        private async Task<IActionResult> BuildProfileViewModel(UserResponse user)
        {
            var managers = await _userService.GetManagersAsync();
            var currentManager = !string.IsNullOrEmpty(user.ManagerId)
                ? managers.FirstOrDefault(m => m.Id == user.ManagerId)
                : null;

            var model = new UserProfileViewModel
            {
                Id = user.Id,
                Email = user.Email,
                FullName = user.FullName,
                IsManager = user.IsManager,
                ManagerId = user.ManagerId,
                ManagerName = currentManager?.FullName,
                IsActive = user.IsActive,
                CreatedAt = user.CreatedAt
            };

            ViewBag.User = _authService.GetCurrentUser();
            return View("Profile", model);
        }
    }
}