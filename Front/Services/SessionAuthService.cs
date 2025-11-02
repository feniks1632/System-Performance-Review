// Services/SessionAuthService.cs
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Services
{
    public interface ISessionAuthService
    {
        void SetUser(UserResponse user);
        UserResponse? GetUser();
        void SetToken(string token);
        string? GetToken();
        void Clear();
        bool IsAuthenticated();
    }

    public class SessionAuthService : ISessionAuthService
    {
        private readonly IHttpContextAccessor _httpContextAccessor;

        public SessionAuthService(IHttpContextAccessor httpContextAccessor)
        {
            _httpContextAccessor = httpContextAccessor;
        }

        public void SetUser(UserResponse user)
        {
            var userJson = System.Text.Json.JsonSerializer.Serialize(user);
            _httpContextAccessor.HttpContext?.Session.SetString("CurrentUser", userJson);
        }

        public UserResponse? GetUser()
        {
            var userJson = _httpContextAccessor.HttpContext?.Session.GetString("CurrentUser");
            if (string.IsNullOrEmpty(userJson)) return null;
            
            return System.Text.Json.JsonSerializer.Deserialize<UserResponse>(userJson);
        }

        public void SetToken(string token)
        {
            _httpContextAccessor.HttpContext?.Session.SetString("JwtToken", token);
        }

        public string? GetToken()
        {
            return _httpContextAccessor.HttpContext?.Session.GetString("JwtToken");
        }

        public void Clear()
        {
            _httpContextAccessor.HttpContext?.Session.Remove("CurrentUser");
            _httpContextAccessor.HttpContext?.Session.Remove("JwtToken");
        }

        public bool IsAuthenticated()
        {
            return !string.IsNullOrEmpty(GetToken()) && GetUser() != null;
        }
    }
}