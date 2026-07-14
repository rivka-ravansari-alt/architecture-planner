# AWS Pricing Validation

This document tracks AWS catalog pricing coverage across all services in the component catalog.

Generate an up-to-date report:

```bash
cd backend
python scripts/aws_pricing_coverage_report.py
python scripts/aws_pricing_coverage_report.py --json
```

## Pipeline (all supported services)

Every **fully supported** AWS component follows the same flow:

1. **Usage assumptions** — LLM or heuristic per-user behavioral inputs (+ `storage_model` for database/object storage)
2. **SKU quantity calculation** — service-specific calculator in `app/pricing/aws/sku_quantities/`
3. **Free tier / included usage** — shared pools in `app/pricing/aws/free_tier.py`
4. **AWS catalog lookup** — Firestore `aws_catalog` unit prices via `AwsCatalogLookup`
5. **Cost calculation** — `AwsCostCalculator`
6. **Component breakdown** — `ComponentCostResult` with SKU line items

**Unsupported** components (e.g. unmapped third-party services) are **not** silently omitted and **not** heuristic-priced. They appear in the pricing output with:

- `pricing_status = "unsupported"`
- `unsupported_reason`
- `missing_implementation` (list of missing pieces)

## Supported services (Group A)

All **26** AWS services in the component catalog are fully supported (Group A). Run the coverage script for the live list.

| Category | Services |
|----------|----------|
| Compute | Lambda, ECS Fargate |
| Data | RDS, DynamoDB, S3, SQS, ElastiCache, OpenSearch Service |
| Platform | API Gateway, CloudFront, Application Load Balancer, Secrets Manager, SSM Parameter Store, AppConfig |
| Messaging | SNS, SES |
| Hosting | Amplify, Amplify Hosting |
| AI | Bedrock |
| Analytics | Athena, QuickSight, CloudWatch Dashboards |
| Observability | CloudWatch, CloudWatch Logs, CloudWatch Alarms, X-Ray |

## Partially supported (Group B)

None at present.

## Missing pricing model (Group C)

None — all catalog AWS services have pricing models.

## Deferred — complex pricing (Group E)

None — previously deferred services now use simplified v1 models. Complex meters (e.g. Bedrock provisioned throughput, QuickSight SPICE, OpenSearch UltraWarm) are documented as warnings on each model.

## Known limitations

- **Default database mapping is DynamoDB** — select RDS explicitly for relational workloads.
- **Heuristic cost bands** (`HeuristicProviderPricing`) apply to **GCP only**, not AWS.
- **LLM usage inference** runs only for fully supported components.
- **RDS PostgreSQL** display name aliases to **RDS** via `normalize_aws_service_name()`.
- **Provisioned DynamoDB capacity**, **PITR**, **streams**, and **global tables** are not modeled.
- **ECS Fargate** has no always-free tier (by design).
- **Bedrock** uses aggregate token meters; model-specific unit prices come from catalog.
- **QuickSight** uses reader/author seat counts; SPICE capacity is not modeled separately.

## Tests

```bash
cd backend
python -m pytest tests/test_aws_pricing_coverage.py -v
python -m pytest tests/test_aws_sku_quantities.py tests/test_aws_catalog_cost.py -v
```

Key assertions:

- Every catalog AWS service has Group A (fully supported) classification
- Unmapped services return `pricing_status=unsupported` (never silent $0)
- Supported services produce SKU line items and catalog-based costs
