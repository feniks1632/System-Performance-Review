using System.ComponentModel.DataAnnotations;
using PerformanceReviewWeb.Models;

namespace PerformanceReviewWeb.Validators
{
    public class FutureDateAttribute : ValidationAttribute
    {
        protected override ValidationResult? IsValid(object? value, ValidationContext validationContext)
        {
            if (value is DateTime date)
            {
                if (date <= DateTime.Now)
                    return new ValidationResult("Дедлайн должен быть в будущем");
            }
            return ValidationResult.Success;
        }
    }

    public class MaxStepsAttribute : ValidationAttribute
    {
        private readonly int _maxSteps;

        public MaxStepsAttribute(int maxSteps)
        {
            _maxSteps = maxSteps;
        }

        protected override ValidationResult? IsValid(object? value, ValidationContext validationContext)
        {
            if (value is List<GoalStepCreateModel> steps)
            {
                if (steps.Count > _maxSteps)
                {
                    return new ValidationResult($"Максимум можно добавить {_maxSteps} подпункта");
                }
            }
            return ValidationResult.Success;
        }
    }
}