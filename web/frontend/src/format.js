export const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
export const fixed = (value, digits = 3) => Number(value).toFixed(digits)

// Chart series colours, tied to the page palette.
export const SERIES = {
  shooter: '#ffcf33', // strike yellow — the shot
  goalkeeper: '#ff6a4d', // save orange — the keeper
  theoretical: '#6fb2c9', // chalk blue — the model
  empirical: '#ffcf33',
}
