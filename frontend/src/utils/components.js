export function partitionIndexedComponents(components) {
  const indexed = components.map((component, index) => ({ ...component, _i: index }));
  return {
    indexed,
    required: indexed.filter((component) => !component.optional),
    optional: indexed.filter((component) => component.optional),
  };
}
