// Models/AnalyticsModels.cs

namespace PerformanceReviewWeb.Models
{
    public class GoalScores
    {
        public double SelfScore { get; set; }
        public double ManagerScore { get; set; }
        public double RespondentScore { get; set; }
        public double TotalScore { get; set; }
    }

    public class GoalAnalyticsResponse
    {
        public string GoalId { get; set; } = string.Empty;
        public string GoalTitle { get; set; } = string.Empty;
        public GoalScores Scores { get; set; } = new GoalScores();
        public string? FinalRating { get; set; } = string.Empty;
        public List<string> Recommendations { get; set; } = new List<string>();
        public int ReviewCount { get; set; }
        public int RespondentCount { get; set; }
        public string? FinalFeedback { get; set; }
    }

    public class EmployeeSummaryResponse
    {
        public string EmployeeId { get; set; } = string.Empty;
        public int TotalGoals { get; set; }
        public int CompletedGoals { get; set; }
        public double AverageScore { get; set; }
        public string OverallRating { get; set; } = string.Empty;
        public List<GoalAnalyticsResponse> GoalsAnalytics { get; set; } = new List<GoalAnalyticsResponse>();
    }
}