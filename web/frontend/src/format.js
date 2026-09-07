export const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
export const fixed = (value, digits = 3) => Number(value).toFixed(digits)

// Chalk-annotation colours, shared by every chart.
export const SERIES = {
  shooter: '#f5b13d', // amber — same as the ball
  goalkeeper: '#dd5a3a', // burnt orange — the keeper
  theoretical: '#82b2c6', // chalk blue
  empirical: '#f5b13d', // amber
}
