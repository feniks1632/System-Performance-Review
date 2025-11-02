// ViewComponents/QuestionOptionsViewComponent.cs
using Microsoft.AspNetCore.Mvc;
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.ViewComponents
{
    public class QuestionOptionsViewComponent : ViewComponent
    {
        public IViewComponentResult Invoke(QuestionTemplateResponse question, string answerValue = "", int questionIndex = 0)
        {
            var selectedOptions = string.IsNullOrEmpty(answerValue) 
                ? new List<string>() 
                : answerValue.Split(',').Select(x => x.Trim()).ToList();

            var model = new QuestionOptionsViewModel
            {
                Question = question,
                SelectedOptions = selectedOptions,
                QuestionIndex = questionIndex
            };

            return View(model);
        }
    }

    public class QuestionOptionsViewModel
    {
        public QuestionTemplateResponse Question { get; set; } = null!;
        public List<string> SelectedOptions { get; set; } = new List<string>();
        public int QuestionIndex { get; set; }
    }
}