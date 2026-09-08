export const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
export const fixed = (value, digits = 3) => Number(value).toFixed(digits)

// Chart series colours, tied to the broadcast palette.
export const SERIES = {
  shooter: '#ffd23f', // signal yellow — same as the ball
  goalkeeper: '#ff6a4d', // alert orange — the keeper
  theoretical: '#7fb2c9', // calm chalk blue
  empirical: '#ffd23f',
}
