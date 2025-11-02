// Models/AuthModels.cs

using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace PerformanceReviewWeb.Models
{
    public class LoginModel
    {
        [Required(ErrorMessage = "Email обязателен")]
        [EmailAddress(ErrorMessage = "Некорректный формат email")]
        public string Email { get; set; } = string.Empty;

        [Required(ErrorMessage = "Пароль обязателен")]
        public string Password { get; set; } = string.Empty;
    }

    public class RegisterModel
    {
        [Required(ErrorMessage = "Email обязателен")]
        [EmailAddress(ErrorMessage = "Некорректный формат email")]
        public string Email { get; set; } = string.Empty;

        [Required(ErrorMessage = "Полное имя обязательно")]
        public string FullName { get; set; } = string.Empty;

        [Required(ErrorMessage = "Пароль обязателен")]
        [MinLength(6, ErrorMessage = "Пароль должен быть не менее 6 символов")]
        public string Password { get; set; } = string.Empty;

        public bool IsManager { get; set; }
        public string? ManagerId { get; set; }
    }

    public class AuthResponse
    {
        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; } = string.Empty;
        
        [JsonPropertyName("token_type")]
        public string TokenType { get; set; } = "bearer";
        
        [JsonPropertyName("user")]
        public UserResponse User { get; set; } = new UserResponse();
    }

    public class UserResponse
    {
        public string Id { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string FullName { get; set; } = string.Empty;
        public bool IsManager { get; set; }
        public bool IsActive { get; set; }
        public string? ManagerId { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    public class TokenResponse
    {
        public string AccessToken { get; set; } = string.Empty;
        public string TokenType { get; set; } = string.Empty;
        public UserResponse User { get; set; } = new UserResponse();
    }
    public class ErrorResponse
    {
        [JsonPropertyName("detail")]
        public string Detail { get; set; } = string.Empty;

        [JsonPropertyName("error")]
        public string Error { get; set; } = string.Empty;

        [JsonPropertyName("message")]
        public string Message { get; set; } = string.Empty;
    }


}