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
  // const highContrastColors: string[] = [
  //   "#FF5733", // Bright Orange
  //   "#FFBD33", // Bright Yellow
  //   "#75FF33", // Bright Lime Green
  //   "#33FF57", // Bright Green
  //   "#33FFBD", // Bright Aqua
  //   "#33D4FF", // Bright Sky Blue
  //   "#3375FF", // Bright Blue
  //   "#7533FF", // Bright Purple
  //   "#BD33FF", // Bright Violet
  //   "#FF33D4", // Bright Magenta
  //   "#FF339F", // Bright Pink
  //   "#FF3357", // Bright Red-Pink
  //   "#FFA533", // Bright Coral
  //   "#33FFA5", // Bright Mint Green
  //   "#33FF75", // Bright Sea Green
  //   "#A5FF33"  // Bright Lime Yellow
  // ];
  const highContrastColors = [
    "#8B0000", // Dark Red
    "#A52A2A", // Brown
    "#800080", // Dark Purple
    "#2F4F4F", // Dark Slate Grey
    "#006400", // Dark Green
    "#556B2F", // Dark Olive Green
    "#8B4513", // Saddle Brown
    "#483D8B", // Dark Slate Blue
    "#2E8B57", // Sea Green
    "#4682B4", // Steel Blue
    "#5F9EA0", // Cadet Blue
    "#708090", // Slate Grey
    "#6A5ACD", // Slate Blue
    "#4B0082", // Indigo
    "#696969", // Dim Grey
    "#B22222"  // Firebrick
  ];

  const seed = metricName
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);

  return highContrastColors[seed % highContrastColors.length];

  const hue = seed % 360;
  return `hsl(${hue}, 70%, 50%)`;
}
