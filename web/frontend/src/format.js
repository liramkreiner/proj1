export const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
export const fixed = (value, digits = 3) => Number(value).toFixed(digits)

// Deterministic colour per series index (broadcast palette).
export const SERIES = {
  shooter: '#39d98a',
  goalkeeper: '#f5a524',
  theoretical: '#6c8cff',
  empirical: '#39d98a',
}
