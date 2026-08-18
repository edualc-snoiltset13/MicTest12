/**
 * Compute the arithmetic mean of an array of numbers.
 *
 * @param {number[]} numbers - The array of numbers to average.
 * @returns {number} The average of the numbers, or 0 if the array is empty.
 */
function average(numbers) {
  if (!numbers || numbers.length === 0) {
    return 0;
  }

  const sum = numbers.reduce((total, value) => total + value, 0);
  return sum / numbers.length;
}

module.exports = average;
