// Services/ApiService.cs
using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PerformanceReviewWeb.Services
{
    public interface IApiService
    {
        Task<T?> GetAsync<T>(string endpoint, bool suppressAuthClear = false);
        Task<T?> PostAsync<T>(string endpoint, object data, bool suppressAuthClear = false);
        Task<T?> PutAsync<T>(string endpoint, object data, bool suppressAuthClear = false);
        Task<bool> DeleteAsync(string endpoint, bool suppressAuthClear = false);
        void SetToken(string token);
        Task SetTokenAsync(string token); // Добавлен асинхронный метод
        void ClearToken();
        bool IsTokenSet();
        string? GetCurrentToken();
    }

    public class ApiService : IApiService
    {
        private readonly HttpClient _httpClient;
        private readonly IHttpContextAccessor _httpContextAccessor;
        private readonly ILoggerService _loggerService;
        private readonly JsonSerializerOptions _jsonOptions;
        private string? _currentToken;
        private bool _isClearingAuth = false;

        public ApiService(
            HttpClient httpClient,
            IHttpContextAccessor httpContextAccessor,
            ILoggerService loggerService)
        {
            _httpClient = httpClient;
            _httpContextAccessor = httpContextAccessor;
            _loggerService = loggerService;

            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
                WriteIndented = false
            };

            _httpClient.BaseAddress = new Uri("http://localhost:8000/api/v1/");
            _httpClient.DefaultRequestHeaders.Accept
                .Add(new MediaTypeWithQualityHeaderValue("application/json"));
            _httpClient.Timeout = TimeSpan.FromSeconds(30);

            InitializeToken();
        }

        private void InitializeToken()
        {
            try
            {
                var token = _httpContextAccessor.HttpContext?.Session.GetString("JwtToken");
                if (!string.IsNullOrEmpty(token))
                {
                    SetToken(token);
                    Console.WriteLine($"[ApiService] Token initialized from session");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ApiService] Error initializing token: {ex.Message}");
            }
        }

        public void SetToken(string token)
        {
            if (!string.IsNullOrEmpty(token) && !_isClearingAuth)
            {
                _currentToken = token;
                _httpClient.DefaultRequestHeaders.Authorization = 
                    new AuthenticationHeaderValue("Bearer", token);
                Console.WriteLine($"[ApiService] Token set in HttpClient");
            }
        }

        public async Task SetTokenAsync(string token)
        {
            if (!string.IsNullOrEmpty(token) && !_isClearingAuth)
            {
                _currentToken = token;
                _httpClient.DefaultRequestHeaders.Authorization = 
                    new AuthenticationHeaderValue("Bearer", token);
                Console.WriteLine($"[ApiService] Token set in HttpClient (async)");
                
                // Добавляем небольшую асинхронную операцию для устранения предупреждения
                await Task.CompletedTask;
            }
        }

        public void ClearToken()
        {
            if (_isClearingAuth) return;
            
            _currentToken = null;
            _httpClient.DefaultRequestHeaders.Authorization = null;
            Console.WriteLine($"[ApiService] Token cleared");
        }

        public bool IsTokenSet()
        {
            return !string.IsNullOrEmpty(_currentToken);
        }

        public string? GetCurrentToken()
        {
            return _currentToken;
        }

        private async Task<T?> ExecuteRequestAsync<T>(
            Func<Task<HttpResponseMessage>> requestFunc,
            string method,
            string endpoint,
            object? data = null,
            bool suppressAuthClear = false)
        {
            var stopwatch = Stopwatch.StartNew();

            try
            {
                SynchronizeToken();

                if (data != null)
                    await _loggerService.LogApiRequestAsync(method, endpoint, data);
                else
                    await _loggerService.LogApiRequestAsync(method, endpoint);

                // Выполняем запрос
                var response = await requestFunc();

                // РУЧНАЯ ОБРАБОТКА РЕДИРЕКТОВ 307
                if (response.StatusCode == HttpStatusCode.TemporaryRedirect)
                {
                    var location = response.Headers.Location;
                    if (location != null)
                    {
                        Console.WriteLine($"[ApiService] Handling 307 redirect from {endpoint} to {location}");

                        // Создаем новый запрос с сохранением заголовков авторизации
                        var redirectRequest = new HttpRequestMessage(HttpMethod.Post, location);

                        // Копируем контент из оригинального запроса
                        if (data != null)
                        {
                            var json = JsonSerializer.Serialize(data, _jsonOptions);
                            redirectRequest.Content = new StringContent(json, Encoding.UTF8, "application/json");
                        }

                        // Копируем заголовок авторизации
                        if (!string.IsNullOrEmpty(_currentToken))
                        {
                            redirectRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _currentToken);
                        }

                        response = await _httpClient.SendAsync(redirectRequest);
                        Console.WriteLine($"[ApiService] After redirect: {response.StatusCode}");
                    }
                }

                var content = await response.Content.ReadAsStringAsync();
                stopwatch.Stop();

                await _loggerService.LogApiResponseAsync(
                    method, endpoint, content,
                    (int)response.StatusCode,
                    response.IsSuccessStatusCode
                );

                Console.WriteLine($"[ApiService] {method} {endpoint} - {response.StatusCode}");

                if (response.StatusCode == HttpStatusCode.Unauthorized)
                {
                    Console.WriteLine($"[ApiService] 401 Unauthorized for {endpoint}");
                    Console.WriteLine($"[ApiService] Current token exists: {!string.IsNullOrEmpty(_currentToken)}");
                    Console.WriteLine($"[ApiService] Response content: {content}");

                    if (!endpoint.StartsWith("auth/") && !suppressAuthClear)
                    {
                        HandleUnauthorizedResponse();
                    }

                    return default;
                }

                return HandleResponse<T>(content, response.StatusCode, response.IsSuccessStatusCode);
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                await _loggerService.LogApiErrorAsync(method, endpoint, ex);
                Console.WriteLine($"[ApiService] Exception in {method} {endpoint}: {ex.Message}");
                return default;
            }
        }

        private void SynchronizeToken()
        {
            try
            {
                var sessionToken = _httpContextAccessor.HttpContext?.Session.GetString("JwtToken");
                
                if (sessionToken != _currentToken && !_isClearingAuth)
                {
                    if (!string.IsNullOrEmpty(sessionToken))
                    {
                        SetToken(sessionToken);
                    }
                    else if (!string.IsNullOrEmpty(_currentToken))
                    {
                        _httpContextAccessor.HttpContext?.Session.SetString("JwtToken", _currentToken);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ApiService] Error synchronizing token: {ex.Message}");
            }
        }

        private void HandleUnauthorizedResponse()
        {
            if (_isClearingAuth) return;
            
            _isClearingAuth = true;
            Console.WriteLine($"[ApiService] Handling unauthorized response - clearing auth data");
            
            try
            {
                // Очищаем токен в HttpClient
                ClearToken();
                
                // Очищаем сессию
                _httpContextAccessor.HttpContext?.Session.Remove("JwtToken");
                _httpContextAccessor.HttpContext?.Session.Remove("CurrentUser");
                
                Console.WriteLine($"[ApiService] Auth data cleared successfully");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ApiService] Error clearing auth data: {ex.Message}");
            }
            finally
            {
                _isClearingAuth = false;
            }
        }

        public async Task<T?> GetAsync<T>(string endpoint, bool suppressAuthClear = false)
        {
            return await ExecuteRequestAsync<T>(async () =>
            {
                // Используем относительный endpoint
                var request = new HttpRequestMessage(HttpMethod.Get, endpoint);

                if (!string.IsNullOrEmpty(_currentToken))
                {
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _currentToken);
                }

                return await _httpClient.SendAsync(request);
            }, "GET", endpoint, null, suppressAuthClear);
        }

        public async Task<T?> PostAsync<T>(string endpoint, object data, bool suppressAuthClear = false)
        {
            return await ExecuteRequestAsync<T>(async () =>
            {
                var json = JsonSerializer.Serialize(data, _jsonOptions);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                Console.WriteLine($"[ApiService] POST to {endpoint}");
                Console.WriteLine($"[ApiService] Auth Header: {_httpClient.DefaultRequestHeaders.Authorization}");
                Console.WriteLine($"[ApiService] Request data length: {json.Length}");

                // ИСПРАВЛЕНИЕ: Убираем создание абсолютного URL через Uri конструктор
                // Вместо этого используем относительный endpoint
                var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
                {
                    Content = content
                };

                // Явно устанавливаем заголовки для каждого запроса
                if (!string.IsNullOrEmpty(_currentToken))
                {
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _currentToken);
                }

                return await _httpClient.SendAsync(request);
            }, "POST", endpoint, data, suppressAuthClear);
        }

        public async Task<T?> PutAsync<T>(string endpoint, object data, bool suppressAuthClear = false)
        {
            return await ExecuteRequestAsync<T>(async () =>
            {
                var json = JsonSerializer.Serialize(data, _jsonOptions);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Используем относительный endpoint вместо создания абсолютного URL
                var request = new HttpRequestMessage(HttpMethod.Put, endpoint)
                {
                    Content = content
                };

                if (!string.IsNullOrEmpty(_currentToken))
                {
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _currentToken);
                }

                return await _httpClient.SendAsync(request);
            }, "PUT", endpoint, data, suppressAuthClear);
        }

        public async Task<bool> DeleteAsync(string endpoint, bool suppressAuthClear = false)
        {
            var result = await ExecuteRequestAsync<object>(async () =>
            {
                // Используем относительный endpoint
                var request = new HttpRequestMessage(HttpMethod.Delete, endpoint);

                if (!string.IsNullOrEmpty(_currentToken))
                {
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _currentToken);
                }

                return await _httpClient.SendAsync(request);
            }, "DELETE", endpoint, null, suppressAuthClear);

            return result != null;
        }

        private T? HandleResponse<T>(string content, HttpStatusCode statusCode, bool isSuccess)
        {
            if (statusCode == HttpStatusCode.NoContent)
                return default;

            try
            {
                if (!isSuccess)
                {
                    Console.WriteLine($"[ApiService] API Error ({statusCode}): {content}");
                    return default;
                }

                return JsonSerializer.Deserialize<T>(content, _jsonOptions);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ApiService] Error deserializing response: {ex.Message}");
                return default;
            }
        }
    }
}