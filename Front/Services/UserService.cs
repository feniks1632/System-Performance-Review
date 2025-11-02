// Services/UserService.cs

using PerformanceReviewWeb.Models;
using System.Text.Json;

namespace PerformanceReviewWeb.Services
{
    public interface IUserService
    {
        Task<List<UserResponse>> GetManagersAsync();
        Task<List<UserResponse>> GetMySubordinatesAsync();
        Task<UserResponse?> GetUserByIdAsync(string userId);
        Task<bool> AssignManagerAsync(string userId, string managedId);
        Task<List<UserResponse>> GetAvailableRespondentsAsync();
        Task<UserResponse?> RefreshCurrentUserAsync();
    }

    public class UserService : IUserService
    {
        private readonly IApiService _apiService;
        private readonly IAuthService _authService;

        public UserService(IApiService apiService, IAuthService authService)
        {
            _apiService = apiService;
            _authService = authService;
        }

        public async Task<List<UserResponse>> GetManagersAsync()
        {
            return await _apiService.GetAsync<List<UserResponse>>("users/managers") ?? new List<UserResponse>();
        }

        public async Task<List<UserResponse>> GetMySubordinatesAsync()
        {
            return await _apiService.GetAsync<List<UserResponse>>("users/my-subordinates") ?? new List<UserResponse>();
        }

        public async Task<UserResponse?> GetUserByIdAsync(string userId)
        {
            return await _apiService.GetAsync<UserResponse>($"users/{userId}");
        }

        public async Task<bool> UserExistsAsync(string userId)
        {
            try
            {
                var user = await GetUserByIdAsync(userId);
                return user != null;
            }
            catch
            {
                return false;
            }
        }

        public async Task<UserResponse?> RefreshCurrentUserAsync()
        {
            var refreshedUser = await _apiService.GetAsync<UserResponse>("auth/me");

            if (refreshedUser != null)
            {
                var userJson = JsonSerializer.Serialize(refreshedUser);

                _authService.GetType().GetMethod("UpdateSessionUser")?.Invoke(_authService, new[] { userJson });
            }
            return refreshedUser;
        }

        public async Task<List<UserResponse>> GetAvailableRespondentsAsync()
        {
            var currentUser = _authService.GetCurrentUser();
            if (currentUser == null) return new List<UserResponse>();

            var availableUsers = new List<UserResponse>();

            // Managers can assign anyone except themselves
            if (currentUser.IsManager)
            {
                var managers = await GetManagersAsync();
                var subordinates = await GetMySubordinatesAsync();

                availableUsers = managers
                    .Concat(subordinates)
                    .Where(u => u.Id != currentUser.Id && u.IsActive)
                    .DistinctBy(u => u.Id)
                    .ToList();
            }
            else
            {
                var managers = await GetManagersAsync();
                availableUsers = managers
                    .Where(u => u.Id != currentUser.Id && u.IsActive)
                    .ToList();
            }

            return availableUsers;
        }

        public async Task<bool> AssignManagerAsync(string userId, string managerId)
        {
            // Просто передаем вызов API
            var result = await _apiService.PutAsync<SuccessResponse>($"users/{userId}/manager?manager_id={managerId}", new { });
            return result != null;
        }
    }
}