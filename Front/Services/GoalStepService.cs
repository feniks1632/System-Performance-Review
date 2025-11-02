// Services/GoalStepService.cs

using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Services
{
    public interface IGoalStepService
    {
        Task<List<GoalStepResponse>> GetGoalStepsAsync(string goalId);
        Task<GoalStepResponse?> CreateGoalStepAsync(string goalId, GoalStepCreateModel model);
        Task<GoalStepResponse?> UpdateGoalStepAsync(string stepId, GoalStepUpdateModel model);
        Task<bool> DeleteGoalStepAsync(string stepId);
        Task<GoalStepResponse?> CompleteGoalStepAsync(string stepId);
        Task<GoalStepResponse?> IncompleteGoalStepAsync(string stepId);
        Task<List<GoalStepResponse>> GetRespondentGoalStepsAsync(string goalId);
    }

    public class GoalStepService : IGoalStepService
    {
        private readonly IApiService _apiService;

        public GoalStepService(IApiService apiService)
        {
            _apiService = apiService;
        }

        public async Task<List<GoalStepResponse>> GetGoalStepsAsync(string goalId)
        {
            return await _apiService.GetAsync<List<GoalStepResponse>>($"goals/{goalId}/steps") ?? new List<GoalStepResponse>();
        }

        public async Task<GoalStepResponse?> CreateGoalStepAsync(string goalId, GoalStepCreateModel model)
        {
            return await _apiService.PostAsync<GoalStepResponse>($"goals/{goalId}/steps", model);
        }

        public async Task<GoalStepResponse?> UpdateGoalStepAsync(string stepId, GoalStepUpdateModel model)
        {
            return await _apiService.PutAsync<GoalStepResponse>($"steps/{stepId}", model);
        }

        public async Task<bool> DeleteGoalStepAsync(string stepId)
        {
            return await _apiService.DeleteAsync($"steps/{stepId}");
        }

        public async Task<GoalStepResponse?> CompleteGoalStepAsync(string stepId)
        {
            return await _apiService.PutAsync<GoalStepResponse>($"steps/{stepId}/complete", new { });
        }

        public async Task<GoalStepResponse?> IncompleteGoalStepAsync(string stepId)
        {
            return await _apiService.PutAsync<GoalStepResponse>($"steps/{stepId}/incomplete", new { });
        }

        public async Task<List<GoalStepResponse>> GetRespondentGoalStepsAsync(string goalId)
        {
            return await _apiService.GetAsync<List<GoalStepResponse>>($"respondent/{goalId}/steps") ?? new List<GoalStepResponse>();
        }
    }
}