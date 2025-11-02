// Controllers/HomeController.cs

using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Services;

namespace PerformanceReviewWeb.Controllers
{
    public class HomeController : Controller
    {
        private readonly IAuthService _authService;
        private readonly IUserService _userService;

        public HomeController(IAuthService authService, IUserService userService)
        {
            _authService = authService;
            _userService = userService;
        }

        public IActionResult Index()
        {
            if (_authService.IsAuthenticated())
            {
                return RedirectToAction("Dashboard");
            }
            return View();
        }

        [Route("dashboard")]
        public async Task<IActionResult> Dashboard()
        {
            var user = _authService.GetCurrentUser();
            ViewBag.User = user;

            if (user?.IsManager == true)
            {
                ViewBag.Manager = await _userService.GetManagersAsync();
            }

            return View();
        }

        [Route("login")]
        public IActionResult Login()
        {
            if (_authService.IsAuthenticated())
            {
                return RedirectToAction("Dashboard");
            }

            return View();
        }

        [HttpPost]
        [Route("login")]
        public async Task<IActionResult> Login(LoginRequest loginModel)
        {
            if (_authService.IsAuthenticated())
            {
                return RedirectToAction("Dashboard");
            }

            if (!ModelState.IsValid)
            {
                return View(loginModel);
            }

            var authResponse = await _authService.LoginAsync(loginModel);
            if (authResponse != null)
            {
                return RedirectToAction("Dashboard");
            }

            ModelState.AddModelError("", "Неверный email или пароль");
            return View(loginModel);
        }

        [Route("register")]
        public async Task<IActionResult> Register()
        {
            if (_authService.IsAuthenticated())
            {
                return RedirectToAction("Dashboard");
            }

            var managers = await _userService.GetManagersAsync();
            ViewBag.Managers = managers;

            return View();
        }

        [HttpPost]
        [Route("register")]
        public async Task<IActionResult> Register(RegisterRequest registerModel)
        {
            if (_authService.IsAuthenticated())
            {
                return RedirectToAction("Dashboard");
            }

            if (!ModelState.IsValid)
            {
                ViewBag.Managers = await _userService.GetManagersAsync();
                return View(registerModel);
            }

            var userResponse = await _authService.RegisterAsync(registerModel);
            if (userResponse != null)
            {
                // После успешной регистрации автоматически логиним пользователя
                var loginModel = new LoginRequest
                {
                    Email = registerModel.Email,
                    Password = registerModel.Password
                };

                var authResponse = await _authService.LoginAsync(loginModel);
                if (authResponse != null)
                {
                    return RedirectToAction("Dashboard");
                }
                else
                {
                    // Регистрация прошла успешно, но автоматический логин не удался
                    // Перенаправляем на страницу логина с сообщением
                    TempData["SuccessMessage"] = "Регистрация прошла успешно! Пожалуйста, войдите в систему.";
                    return RedirectToAction("Login");
                }
            }

            ModelState.AddModelError("", "Ошибка регистрации. Возможно, пользователь с таким email уже существует.");
            ViewBag.Managers = await _userService.GetManagersAsync();
            return View(registerModel);
        }

        [Route("logout")]
        public IActionResult Logout()
        {
            _authService.Logout();
            return RedirectToAction("Index");
        }

        [Route("profile")]
        public async Task<IActionResult> Profile()
        {
            if (!_authService.IsAuthenticated())
            {
                return RedirectToAction("Login");
            }

            // Получаем актуальные данные профиля
            var user = await _authService.GetCurrentUserProfileAsync();
            if (user == null)
            {
                // Если не удалось получить профиль, разлогиниваем
                _authService.Logout();
                return RedirectToAction("Login");
            }

            ViewBag.User = user;
            return View();
        }
    }
}