using PerformanceReviewWeb.Services;
using PerformanceReviewWeb.Hubs;
using System.Net.Http.Headers;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllersWithViews();
builder.Services.AddHttpClient<IApiService, ApiService>(client =>
{
    client.BaseAddress = new Uri("http://localhost:8000/api/v1");
    client.DefaultRequestHeaders.Accept.Add(
        new MediaTypeWithQualityHeaderValue("application/json"));
    client.Timeout = TimeSpan.FromSeconds(30);
}).ConfigurePrimaryHttpMessageHandler(() => new HttpClientHandler
{
    AllowAutoRedirect = false, // ОТКЛЮЧАЕМ автоматические редиректы
    UseCookies = false,
    CheckCertificateRevocationList = false
});

builder.Services.AddHttpContextAccessor();
builder.Services.AddSignalR();

builder.Services.AddDistributedMemoryCache();
builder.Services.AddSession(options =>
{
    options.IdleTimeout = TimeSpan.FromHours(2); // Увеличиваем время сессии
    options.Cookie.HttpOnly = true;
    options.Cookie.IsEssential = true;
    options.Cookie.SameSite = SameSiteMode.Strict;
    options.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
});

// Register services in correct order to avoid circular dependencies
builder.Services.AddScoped<ILoggerService, LoggerService>();
builder.Services.AddScoped<ISessionAuthService, SessionAuthService>(); // Добавляем новый сервис
builder.Services.AddScoped<IApiService, ApiService>(); // Используем улучшенную версию
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<INotificationService, NotificationService>();
builder.Services.AddScoped<IReviewService, ReviewService>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddScoped<IGoalStepService, GoalStepService>();
builder.Services.AddScoped<IRealTimeNotificationService, RealTimeNotificationService>();
var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();

app.UseRouting();
app.UseSession(); // Session должен быть до UseRouting и UseEndpoints

// Улучшенный authentication middleware
app.Use(async (context, next) =>
{
    try
    {
        var sessionAuthService = context.RequestServices.GetRequiredService<ISessionAuthService>();
        var authService = context.RequestServices.GetRequiredService<IAuthService>();
        
        if (authService.IsAuthenticated())
        {
            var user = authService.GetCurrentUser();
            if (user != null)
            {
                context.Items["User"] = user;
                
                // Синхронизируем токен с ApiService
                var apiService = context.RequestServices.GetRequiredService<IApiService>();
                var token = authService.GetToken();
                if (!string.IsNullOrEmpty(token) && !apiService.IsTokenSet())
                {
                    await apiService.SetTokenAsync(token);
                    Console.WriteLine($"[Middleware] Token synchronized to ApiService");
                }

                // Логируем для отладки
                if (app.Environment.IsDevelopment())
                {
                    Console.WriteLine($"[Middleware] User authenticated: {user.FullName} ({user.Id})");
                }
            }
        }
        else
        {
            // Очищаем данные если пользователь не аутентифицирован
            context.Items["User"] = null;
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[Middleware Error] {ex.Message}");
    }

    await next();
});

app.UseAuthorization();

// Map SignalR hub FIRST - before controllers
app.MapHub<NotificationHub>("/notificationHub");

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

// Health check endpoint для проверки статуса авторизации
app.MapGet("/auth/status", (IAuthService authService) =>
{
    var isAuthenticated = authService.IsAuthenticated();
    var user = authService.GetCurrentUser();
    
    return new
    {
        authenticated = isAuthenticated,
        user = user != null ? new { user.Id, user.FullName, user.Email } : null,
        tokenExists = !string.IsNullOrEmpty(authService.GetToken())
    };
});

app.Run();