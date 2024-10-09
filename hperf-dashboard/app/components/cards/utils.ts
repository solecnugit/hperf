export function autoFormat(value: number) {
  if (value > 1e9)
    return value.toExponential(2)

  let valueStr
  if (Number.isInteger(value))
    valueStr = value.toString()
  else
    valueStr = value.toFixed(2)

  return valueStr.replace(/\B(?=(\d{3})+(?!\d))/g, ",")
}

export function formatGHz(value: number) {
  return (value / 1e9).toFixed(2) + " GHz";
}

export function formatBandwidth(value: number) {
  if (value > 1e9) {
    return `${(value / 1e9).toFixed(2)} Gbps`;
  } else if (value > 1e6) {
    return `${(value / 1e6).toFixed(2)} Mbps`;
  } else if (value > 1e3) {
    return `${(value / 1e3).toFixed(2)} Kbps`;
  } else {
    return `${value.toFixed(2)} bps`;
  }
}

let colorIndex = 0;

export function getColorFrom(metricName: string) {
  const highContrastColors: string[] = [
    "#FF5733", // Bright Orange
    "#FFBD33", // Bright Yellow
    "#75FF33", // Bright Lime Green
    "#33FF57", // Bright Green
    "#33FFBD", // Bright Aqua
    "#33D4FF", // Bright Sky Blue
    "#3375FF", // Bright Blue
    "#7533FF", // Bright Purple
    "#BD33FF", // Bright Violet
    "#FF33D4", // Bright Magenta
    "#FF339F", // Bright Pink
    "#FF3357", // Bright Red-Pink
    "#FFA533", // Bright Coral
    "#33FFA5", // Bright Mint Green
    "#33FF75", // Bright Sea Green
    "#A5FF33"  // Bright Lime Yellow
  ];

  const seed = metricName
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);

  return highContrastColors[seed % highContrastColors.length];

  const hue = seed % 360;
  return `hsl(${hue}, 70%, 50%)`;
}
