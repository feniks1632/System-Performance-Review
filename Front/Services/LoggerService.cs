// Services/LoggerService.cs

using System.Text.Json;

namespace PerformanceReviewWeb.Services
{
    public interface ILoggerService
    {
        Task LogApiRequestAsync(string method, string endpoint, object? data = null);
        Task LogApiResponseAsync(string method, string endpoint, string responseContent, int statusCode, bool isSuccess);
        Task LogApiErrorAsync(string method, string endpoint, Exception exception);
        Task<List<ApiLogEntry>> GetRecentLogsAsync(int count = 50);
        Task ClearLogsAsync();
        Task<int> GetTotalCountAsync();
        Task<int> GetSuccessCountAsync();
        Task<int> GetErrorCountAsync();
    }

    public class LoggerService : ILoggerService
    {
        private readonly List<ApiLogEntry> _logs = new List<ApiLogEntry>();
        private readonly int _maxLogs = 1000;
        private readonly SemaphoreSlim _semaphore = new SemaphoreSlim(1, 1);
        private readonly JsonSerializerOptions _jsonOptions;

        public LoggerService()
        {
            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
            };
        }

        public async Task LogApiRequestAsync(string method, string endpoint, object? data = null)
        {
            await _semaphore.WaitAsync();
            try
            {
                var logEntry = new ApiLogEntry
                {
                    Id = Guid.NewGuid().ToString(),
                    Timestamp = DateTime.Now,
                    Method = method.ToUpperInvariant(),
                    Endpoint = endpoint,
                    ResponseBody = SerializeData(data),
                    Type = LogType.Request,
                    StatusCode = 0,
                    IsSuccess = false
                };

                AddLogEntry(logEntry);

                Console.ForegroundColor = ConsoleColor.Blue;
                Console.WriteLine($"[{logEntry.Timestamp:HH:mm:ss}] 📤 {method} {endpoint}");
                if (!string.IsNullOrEmpty(logEntry.RequestBody) && logEntry.RequestBody != "null")
                {
                    Console.WriteLine($"   Body: {logEntry.RequestBody}");
                }
                Console.ResetColor();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task LogApiResponseAsync(string method, string endpoint, string responseContent, int statusCode, bool isSuccess)
        {
            await _semaphore.WaitAsync();
            try
            {
                var logEntry = new ApiLogEntry
                {
                    Id = Guid.NewGuid().ToString(),
                    Timestamp = DateTime.Now,
                    Method = method.ToUpperInvariant(),
                    Endpoint = endpoint,
                    ResponseBody = responseContent.Length > 2000 ? responseContent[..2000] + "..." : responseContent,
                    StatusCode = statusCode,
                    IsSuccess = isSuccess,
                    Type = LogType.Response
                };

                AddLogEntry(logEntry);

                var color = isSuccess ? ConsoleColor.Green : ConsoleColor.Red;
                Console.ForegroundColor = color;
                Console.WriteLine($"[{logEntry.Timestamp:HH:mm:ss}] 📥 {statusCode} {method} {endpoint}");
                if (!string.IsNullOrEmpty(responseContent) && responseContent.Length < 500)
                {
                    Console.WriteLine($"   Response: {responseContent}");
                }
                Console.ResetColor();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task LogApiErrorAsync(string method, string endpoint, Exception exception)
        {
            await _semaphore.WaitAsync();
            try
            {
                var logEntry = new ApiLogEntry
                {
                    Id = Guid.NewGuid().ToString(),
                    Timestamp = DateTime.Now,
                    Method = method.ToUpperInvariant(),
                    Endpoint = endpoint,
                    ResponseBody = $"Exception: {exception.Message}\nStackTrace: {exception.StackTrace}",
                    StatusCode = 0,
                    IsSuccess = false,
                    Type = LogType.Error
                };

                AddLogEntry(logEntry);

                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"[{logEntry.Timestamp:HH:mm:ss}] ❌ ERROR {method} {endpoint}");
                Console.WriteLine($"   {exception.Message}");
                if (exception.InnerException != null)
                {
                    Console.WriteLine($"   Inner: {exception.InnerException.Message}");
                }
                Console.ResetColor();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<List<ApiLogEntry>> GetRecentLogsAsync(int count = 100)
        {
            await _semaphore.WaitAsync();
            try
            {
                return _logs
                    .OrderByDescending(x => x.Timestamp)
                    .Take(count)
                    .ToList();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task ClearLogsAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                _logs.Clear();
                Console.WriteLine("🧹 All logs cleared");
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<int> GetTotalCountAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                return _logs.Count;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<int> GetSuccessCountAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                return _logs.Count(x => x.IsSuccess);
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<int> GetErrorCountAsync()
        {
            await _semaphore.WaitAsync();
            try
            {
                return _logs.Count(x => !x.IsSuccess && x.StatusCode > 0);
            }
            finally
            {
                _semaphore.Release();
            }
        }

        private void AddLogEntry(ApiLogEntry entry)
        {
            _logs.Add(entry);
            
            // Ограничиваем количество логов в памяти
            if (_logs.Count > _maxLogs)
            {
                _logs.RemoveRange(0, _logs.Count - _maxLogs);
            }
        }

        private string? SerializeData(object? data)
        {
            if (data == null) return null;
            
            try
            {
                return JsonSerializer.Serialize(data, _jsonOptions);
            }
            catch (Exception ex)
            {
                return $"Serialization error: {ex.Message}";
            }
        }
    }

    public class ApiLogEntry
    {
        public string Id { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
        public string Method { get; set; } = string.Empty;
        public string Endpoint { get; set; } = string.Empty;
        public string? RequestBody { get; set; }
        public string? ResponseBody { get; set; }
        public int StatusCode { get; set; }
        public bool IsSuccess { get; set; }
        public LogType Type { get; set; }
        public TimeSpan Duration { get; set; }
    }

    public enum LogType
    {
        Request,
        Response,
        Error
    }
}