export const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
export const fixed = (value, digits = 3) => Number(value).toFixed(digits)

// Chart series colours — the matchday palette.
export const SERIES = {
  shooter: '#1c7a3e', // pitch green — the striker
  goalkeeper: '#df3b26', // vermilion — the keeper
  theoretical: '#d9982a', // ochre — the model
  empirical: '#1c7a3e',
}
