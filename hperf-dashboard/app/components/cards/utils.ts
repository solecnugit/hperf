export function autoFormat(value: number) {
  if (value > 1e9) {
    // format with scientific notation
    return value.toExponential(2);
  }

  return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
