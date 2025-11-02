// Services/AuthService.cs
using System.Text.Json;
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Services
{
    public interface IAuthService
    {
        Task<AuthResponse?> LoginAsync(LoginRequest loginRequest);
        Task<UserResponse?> RegisterAsync(RegisterRequest registerRequest);
        void Logout();
        bool IsAuthenticated();
        UserResponse? GetCurrentUser();
        string? GetToken();
        Task<UserResponse?> GetCurrentUserProfileAsync();
    }

    public class AuthService : IAuthService
    {
        private readonly IApiService _apiService;
        private readonly ISessionAuthService _sessionAuthService;

        public AuthService(IApiService apiService, ISessionAuthService sessionAuthService)
        {
            _apiService = apiService;
            _sessionAuthService = sessionAuthService;
        }

        public async Task<AuthResponse?> LoginAsync(LoginRequest request)
        {
            try
            {
                Console.WriteLine($"[AuthService] Attempting login for: {request.Email}");

                // Временно очищаем токен для запроса логина
                _apiService.ClearToken();
                
                var response = await _apiService.PostAsync<AuthResponse>("auth/login", request);

                if (response != null && !string.IsNullOrEmpty(response.AccessToken))
                {
                    Console.WriteLine($"[AuthService] Login successful, token received");
                    
                    // Сохраняем через SessionAuthService
                    _sessionAuthService.SetToken(response.AccessToken);
                    _sessionAuthService.SetUser(response.User);
                    
                    // Устанавливаем токен в ApiService
                    _apiService.SetToken(response.AccessToken);
                    
                    Console.WriteLine($"[AuthService] User {response.User.FullName} logged in successfully");
                    return response;
                }
                
                Console.WriteLine($"[AuthService] Login failed - invalid response");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[AuthService] Login error: {ex.Message}");
                Logout();
                return null;
            }
        }

        public async Task<UserResponse?> RegisterAsync(RegisterRequest request)
        {
            try
            {
                _apiService.ClearToken();
                var response = await _apiService.PostAsync<UserResponse>("auth/register", request);
                
                if (response != null)
                {
                    Console.WriteLine($"[AuthService] Registration successful for: {response.Email}");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[AuthService] Register error: {ex.Message}");
                return null;
            }
        }

        public void Logout()
        {
            Console.WriteLine($"[AuthService] Logging out user");
            _sessionAuthService.Clear();
            _apiService.ClearToken();
            Console.WriteLine($"[AuthService] Logout completed");
        }

        public bool IsAuthenticated()
        {
            return _sessionAuthService.IsAuthenticated();
        }

        public UserResponse? GetCurrentUser()
        {
            return _sessionAuthService.GetUser();
        }

        public string? GetToken()
        {
            return _sessionAuthService.GetToken();
        }

        public async Task<UserResponse?> GetCurrentUserProfileAsync()
        {
            if (!IsAuthenticated())
            {
                Console.WriteLine($"[AuthService] Cannot get profile - not authenticated");
                return null;
            }

            try
            {
                var user = await _apiService.GetAsync<UserResponse>("auth/me");
                if (user != null)
                {
                    // Обновляем данные пользователя в сессии
                    _sessionAuthService.SetUser(user);
                    Console.WriteLine($"[AuthService] User profile updated successfully");
                    return user;
                }
                
                Console.WriteLine($"[AuthService] Failed to get user profile - API returned null");
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[AuthService] Get profile error: {ex.Message}");
                return null;
            }
        }
    }

    // DTO классы для запросов и ответов
    public class LoginRequest
    {
        public string Email { get; set; } = string.Empty;
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterRequest
    {
        public string Email { get; set; } = string.Empty;
        public string FullName { get; set; } = string.Empty;
        public bool IsManager { get; set; }
        public string Password { get; set; } = string.Empty;
        public string? ManagerId { get; set; }
    }

    public class AuthResponse
    {
        public string AccessToken { get; set; } = string.Empty;
        public string TokenType { get; set; } = "bearer";
        public UserResponse User { get; set; } = new UserResponse();
    }
}