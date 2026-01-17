/**
 * Transforms a 2D array (first row = header) into an object
 * with `time` and `profit` arrays, suitable for charting.
 *
 * @param {Array[]} data
 *   - data[0] is the header row
 *   - data[i][3] is the Date/Time value
 *   - data[i][6] is the Profit USD value
 * @returns {{time: number[], profit: number[]}}
 */
function transformToTimeProfitForChart(data) {
  // start balance
  const startBalance = 0;
  let cumulative = startBalance;

  // validate
  if (!data || !Array.isArray(data) || data.length < 2) {
    console.error("Invalid data for chart transformation.");
    return { time: [], profit: [startBalance] };
  }

  const theader = data[0];

  const tIndex = theader.indexOf("Date/Time");
  const pIndexName = theader.find(
    (text) =>
      ["Net P&L", "Profit"].some((keyword) => text.includes(keyword)) &&
      !text.includes("%")
  );
  const pIndex = theader.indexOf(pIndexName);

  if (tIndex === -1 || pIndex === -1) {
    console.error("Required columns not found in header.");
    return { time: [], profit: [startBalance] };
  }

  // skip header and filter only exit rows
  const rows = data.slice(1);

  const exitRows = rows.filter(
    (row) =>
      typeof row[1] === "string" && row[1].toLowerCase().startsWith("exit")
  );

  // console.log("Exit rows:", exitRows);

  // prepare arrays
  const time = [];
  const profit = [startBalance];

  // accumulate profit
  exitRows.forEach((row) => {
    let t = row[tIndex];
    const p = parseFloat(row[pIndex]) || 0;
    cumulative += p;
    time.push(t);
    profit.push(cumulative);
  });

  // console.log("Transformed series:", { time, profit });

  return { time, profit };
}

function getChartOptions(tooltipCallbacks, xAxis = false, yAxis = false) {
  return {
    animation: false,
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: 0,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: true,
        position: "nearest",
        // caretPadding: 20, // distance from line
        // boxPaadding: 6, // padding inside tooltip box
        // yAlign: "center", // force tooltip above point
        // xAlign: "left", // force tooltip to the right of point
        displayColors: false,
        backgroundColor: getCssVariableColor("--color-background"),
        titleColor: getCssVariableColor("--color-title"),
        bodyColor: getCssVariableColor("--color-text"),
        padding: 12,
        cornerRadius: 4,
        callbacks: tooltipCallbacks,
      },
    },
    interaction: {
      mode: "index",
      intersect: false,
      axis: "x",
    },
    scales: {
      x: {
        display: xAxis,
        grid: { display: false, drawBorder: false },
        border: { display: false },
        ticks: {
          color: getCssVariableColor("--color-text", 0.6),
          font: {
            size: 10,
          },

          maxRotation: 0,
          minRotation: 0,
          callback: function (value, index, ticks) {
            const date = new Date(this.getLabelForValue(value));
            const monthNames = [
              "Jan",
              "Feb",
              "Mar",
              "Apr",
              "May",
              "Jun",
              "Jul",
              "Aug",
              "Sep",
              "Oct",
              "Nov",
              "Dec",
            ];
            const month = date.getUTCMonth();
            const day = date.getUTCDate();

            // Check previous tick to see if it's the same month
            // Limit to max 4-5 ticks by calculating step
            const totalTicks = ticks.length;
            const maxTicks = 5;
            const step = Math.ceil(totalTicks / maxTicks);

            // Only show tick if it's at the right step interval
            if (index % step !== 0 && index !== totalTicks - 1) {
              return ""; // Skip this tick
            }

            if (index === ticks.length - 1) {
              // Always show last tick
              return ``;
            }

            if (index > 0) {
              const prevDate = new Date(
                this.getLabelForValue(ticks[index - 1].value)
              );
              const prevMonth = prevDate.getUTCMonth();
              if (month === prevMonth) {
                // return ""; // Skip this tick
              }
            }

            return `${monthNames[month]} ${day}`;
          },
        },
      },
      y: {
        display: yAxis,
        position: "right",
        grid: { display: false, drawBorder: false },
        border: { display: false },
        ticks: {
          color: getCssVariableColor("--color-text", 0.6),
          font: {
            size: 10,
          },
          callback: function (value, index, ticks) {
            const totalTicks = ticks.length;
            const maxTicks = 5;
            const step = Math.ceil(totalTicks / maxTicks);

            // Only show tick if it's at the right step interval
            if (index % step !== 0 && index !== totalTicks - 1) {
              return ""; // Skip this tick
            }

            if (index === ticks.length - 1) {
              // Always show last tick
              return ``;
            }

            return value;
          },
        },
      },
    },
  };
}

function getPlugins() {
  // Create custom plugin for vertical line
  const verticalLinePlugin = {
    id: "verticalLine",
    beforeDatasetsDraw: (chart) => {
      if (chart.tooltip?._active?.length) {
        const ctx = chart.ctx;
        const activePoint = chart.tooltip._active[0];
        const x = activePoint.element.x;
        const topY = chart.scales.y.top;
        const bottomY = chart.scales.y.bottom;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(x, topY);
        ctx.lineTo(x, bottomY);
        ctx.lineWidth = 1;
        ctx.strokeStyle = getCssVariableColor("--color-text", 0.2);
        ctx.stroke();
        ctx.restore();
      }
    },
  };
  return [verticalLinePlugin];
}

function loadChart(id) {
  const ctx = document.getElementById("profitChart-" + id).getContext("2d");
  // `data` should be your original 2D data array; transform it with your helper function
  // Safely escape Django JSON for inclusion in JS
  const raw = document.getElementById("trades-data-" + id).textContent;
  const data = JSON.parse(raw);

  // Destroy existing chart instance if it exists
  const existingChart = Chart.getChart("profitChart-" + id);
  if (existingChart) {
    existingChart.destroy();
  }
  const series = transformToTimeProfitForChart(data);
  const minValue = Math.min(...series.profit);

  new Chart(ctx, {
    type: "line",
    data: {
      labels: series.time,
      datasets: [
        {
          data: series.profit,
          borderWidth: 1.5,
          fill: true,
          // scriptable border color per line segment based on profit sign
          borderColor: function (context) {
            const value = context.dataset.data[context.dataIndex];
            return value < 0
              ? getCssVariableColor("--color-loss")
              : getCssVariableColor("--color-profit");
          },
          // color the segment between points based on the end value
          segment: {
            borderColor: (ctx) => {
              const p1 = ctx.p1.parsed.y;
              return p1 < 0
                ? getCssVariableColor("--color-loss")
                : getCssVariableColor("--color-profit");
            },
            backgroundColor: (ctx) => {
              const y = ctx.p1.parsed.y;
              // return semi-transparent fill per segment
              return y < 0
                ? getCssVariableColor("--color-loss", 0.04)
                : getCssVariableColor("--color-profit", 0.04);
            },
          },
          pointRadius: 0,
          pointHoverRadius: 0,
          pointHitRadius: 10,
        },
      ],
    },
    options: getChartOptions({
      title: (tooltipItems) => {
        // Parse Excel serial (assuming UTC) to JS Date
        const serial = parseFloat(tooltipItems[0].label);
        // Excel epoch starts at 1899-12-30
        const utcDays = serial - 25569;
        const utcMs = utcDays * 86400 * 1000;
        const date = new Date(utcMs);
        // Month names for display
        const monthNames = [
          "Jan",
          "Feb",
          "Mar",
          "Apr",
          "May",
          "Jun",
          "Jul",
          "Aug",
          "Sep",
          "Oct",
          "Nov",
          "Dec",
        ];
        // Helper to pad numbers
        const pad = (n) => (n < 10 ? "0" + n : n);
        const year = date.getUTCFullYear();
        const month = monthNames[date.getUTCMonth()];
        const day = pad(date.getUTCDate());
        const hours = pad(date.getUTCHours());
        const minutes = pad(date.getUTCMinutes());
        return `${day} ${month} ${year}   ${hours}:${minutes}`;
      },
      label: (tooltipItem) => {
        // Display the profit value
        return `Profit: ${tooltipItem.formattedValue}`;
      },
    }),
    plugins: getPlugins(),
  });
}

function loadAccountProfitCharts(id, data) {
  const ctx = document.getElementById(id).getContext("2d");

  // console.log("Loading chart with data:", data);

  labels = data.map((item) => item.date);
  profitData = data.map((item) => item.total_net_profit);

  const series = {
    date: labels,
    net_profit: profitData,
    daily_net_profit: data.map((item) => item.today_net_profit),
    daily_trades: data.map((item) => item.today_trades),
  };

  const existingChart = Chart.getChart(id);
  if (existingChart) {
    existingChart.destroy();
  }

  new Chart(ctx, {
    type: "line",
    data: {
      labels: series.date,
      datasets: [
        {
          data: series.net_profit,
          borderWidth: 1.5,
          fill: true,
          borderColor: function (context) {
            const value = context.dataset.data[context.dataIndex];
            return value < 0
              ? getCssVariableColor("--color-loss")
              : getCssVariableColor("--color-profit");
          },
          segment: {
            borderColor: (ctx) => {
              const p1 = ctx.p1.parsed.y;
              return p1 < 0
                ? getCssVariableColor("--color-loss")
                : getCssVariableColor("--color-profit");
            },
            backgroundColor: (ctx) => {
              const y = ctx.p1.parsed.y;
              return y < 0
                ? getCssVariableColor("--color-loss", 0.04)
                : getCssVariableColor("--color-profit", 0.04);
            },
          },
          pointRadius: 0,
          pointHoverRadius: 0,
          pointHitRadius: 10,
          tension: 0.1,
        },
      ],
    },
    options: getChartOptions(
      {
        title: (tooltipItems) => {
          return tooltipItems[0].label;
        },
        label: (tooltipItem) => {
          const profit = `Cumulative net PnL: ${tooltipItem.formattedValue}`;
          const dailyProfit = `Net PnL: ${
            series.daily_net_profit[tooltipItem.dataIndex]
          }`;
          const dailyTrades = `Trades: ${
            series.daily_trades[tooltipItem.dataIndex]
          }`;
          return [profit, dailyProfit, dailyTrades];
        },
      },
      true,
      true
    ),
    plugins: getPlugins(),
  });
}

/**
 * Creates a radar chart for comparing two datasets (e.g., Buy vs Sell)
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} options - Configuration object
 * @param {string[]} options.labels - Array of labels for each axis
 * @param {Object} options.dataset1 - First dataset config { label, data, color }
 * @param {Object} options.dataset2 - Second dataset config { label, data, color }
 * @returns {Chart|null} - The Chart instance or null if canvas not found
 */
function loadRadarChart(canvasId, options) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const existingChart = Chart.getChart(canvasId);
  if (existingChart) existingChart.destroy();

  const textColor = getCssVariableColor("--color-text");

  // Default colors if not provided
  const color1 =
    options.dataset1.color || getCssVariableColor("--color-primary");
  const color2 =
    options.dataset2.color || getCssVariableColor("--color-accent");

  return new Chart(ctx, {
    type: "radar",
    data: {
      labels: options.labels,
      datasets: [
        {
          label: options.dataset1.label || "Dataset 1",
          data: options.dataset1.data,
          backgroundColor: color1 + "33",
          borderColor: color1,
          borderWidth: 2,
          pointBackgroundColor: color1,
          pointBorderColor: color1,
          pointRadius: 4,
        },
        {
          label: options.dataset2.label || "Dataset 2",
          data: options.dataset2.data,
          backgroundColor: color2 + "33",
          borderColor: color2,
          borderWidth: 2,
          pointBackgroundColor: color2,
          pointBorderColor: color2,
          pointRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: getCssVariableColor("--color-background"),
          titleColor: getCssVariableColor("--color-title"),
          bodyColor: getCssVariableColor("--color-text"),
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
        },
      },
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: textColor + "15" },
          angleLines: { color: textColor + "15" },
          pointLabels: {
            color: textColor + "80",
            font: { size: 10 },
          },
          ticks: { display: false },
        },
      },
    },
  });
}

/**
 * Creates a Buy vs Sell radar chart with predefined styling
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} buyData - Buy trades data { winRate, winners, losers, total }
 * @param {Object} sellData - Sell trades data { winRate, winners, losers, total }
 * @returns {Chart|null} - The Chart instance or null if canvas not found
 */
function loadBuySellRadarChart(canvasId, buyData, sellData) {
  const primaryColor = getCssVariableColor("--color-primary");
  const sellColor = getCssVariableColor("--color-loss");

  return loadRadarChart(canvasId, {
    labels: ["Win Rate", "Winners", "Losers", "Total"],
    dataset1: {
      label: "Buy",
      data: [buyData.winRate, buyData.winners, buyData.losers, buyData.total],
      color: primaryColor,
    },
    dataset2: {
      label: "Sell",
      data: [
        sellData.winRate,
        sellData.winners,
        sellData.losers,
        sellData.total,
      ],
      color: sellColor,
    },
  });
}

/**
 * Creates a polar area chart for trade breakdown
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} data - Object containing trade counts { buyWins, buyLosses, sellWins, sellLosses }
 * @returns {Chart|null} - The Chart instance or null if canvas not found
 */
function loadPolarAreaChart(canvasId, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const existingChart = Chart.getChart(canvasId);
  if (existingChart) existingChart.destroy();

  const profitColor = getCssVariableColor("--color-profit");
  const lossColor = getCssVariableColor("--color-loss");
  const primaryColor = getCssVariableColor("--color-primary");

  return new Chart(ctx, {
    type: "polarArea",
    data: {
      labels: ["Buy Wins", "Buy Losses", "Sell Wins", "Sell Losses"],
      datasets: [
        {
          data: [data.buyWins, data.buyLosses, data.sellWins, data.sellLosses],
          backgroundColor: [
            primaryColor + "99",
            lossColor + "99",
            profitColor + "77",
            lossColor + "55",
          ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: getCssVariableColor("--color-background"),
          titleColor: getCssVariableColor("--color-title"),
          bodyColor: getCssVariableColor("--color-text"),
          padding: 12,
          cornerRadius: 8,
          displayColors: true,
        },
      },
      scales: {
        r: { display: false },
      },
    },
  });
}
