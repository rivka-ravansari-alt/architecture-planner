"""Dispatch AWS SKU quantity calculators by service."""

from __future__ import annotations

from app.pricing.aws.sku_quantities.api_gateway import calculate_api_gateway_quantities
from app.pricing.aws.sku_quantities.application_load_balancer import calculate_alb_quantities
from app.pricing.aws.sku_quantities.cloudfront import calculate_cloudfront_quantities
from app.pricing.aws.sku_quantities.dynamodb import calculate_dynamodb_quantities
from app.pricing.aws.sku_quantities.ecs_fargate import calculate_ecs_fargate_quantities
from app.pricing.aws.sku_quantities.lambda_service import calculate_lambda_quantities
from app.pricing.aws.sku_quantities.rds import calculate_rds_quantities
from app.pricing.aws.sku_quantities.s3 import calculate_s3_quantities
from app.pricing.aws.sku_quantities.extended import EXTENDED_AWS_SKU_CALCULATORS
from app.pricing.aws.sku_quantities.secrets_manager import calculate_secrets_manager_quantities
from app.pricing.aws.sku_quantities.sns import calculate_sns_quantities
from app.pricing.aws.sku_quantities.sqs import calculate_sqs_quantities
from app.pricing.schemas import AwsServicePricingModel, SkuQuantityResult, UsageAssumption

_CALCULATORS = {
    "Lambda": calculate_lambda_quantities,
    "ECS Fargate": calculate_ecs_fargate_quantities,
    "RDS": calculate_rds_quantities,
    "DynamoDB": calculate_dynamodb_quantities,
    "S3": calculate_s3_quantities,
    "SQS": calculate_sqs_quantities,
    "API Gateway": calculate_api_gateway_quantities,
    "SNS": calculate_sns_quantities,
    "CloudFront": calculate_cloudfront_quantities,
    "Application Load Balancer": calculate_alb_quantities,
    "Secrets Manager": calculate_secrets_manager_quantities,
    **EXTENDED_AWS_SKU_CALCULATORS,
}


def calculate_aws_sku_quantities(
    model: AwsServicePricingModel,
    resolved: list[UsageAssumption],
) -> SkuQuantityResult:
    """Convert resolved usage assumptions into deterministic SKU quantities."""
    calculator = _CALCULATORS.get(model.service)
    if calculator is None:
        return SkuQuantityResult(
            service=model.service,
            quantities=[],
            missing=[],
            ready=False,
        )
    return calculator(model, resolved)
