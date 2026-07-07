function formatUsd(value) {
  return `$${Number(value ?? 0).toLocaleString(undefined, {
    minimumFractionDigits: Number.isInteger(Number(value)) ? 0 : 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatCostRange(low, high) {
  const lowValue = Number(low ?? 0);
  const highValue = Number(high ?? lowValue);

  if (lowValue === 0 && highValue === 0) {
    return "—";
  }
  if (Math.abs(highValue - lowValue) < 0.005) {
    return formatUsd(lowValue);
  }
  return `${formatUsd(lowValue)} – ${formatUsd(highValue)}`;
}

export function formatOptionalCostRange(low, high) {
  const lowValue = Number(low ?? 0);
  const highValue = Number(high ?? lowValue);

  if (lowValue === 0 && highValue === 0) {
    return "—";
  }
  if (Math.abs(highValue - lowValue) < 0.005) {
    return `+${formatUsd(lowValue)}`;
  }
  return `+${formatUsd(lowValue)} – ${formatUsd(highValue)}`;
}

export function formatProviderCostLabel(cost) {
  return formatCostRange(
    cost.monthly_low ?? cost.totalLow ?? cost.requiredLow,
    cost.monthly_high ?? cost.totalHigh ?? cost.requiredHigh
  );
}
