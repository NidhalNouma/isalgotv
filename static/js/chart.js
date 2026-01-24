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
 * Renders a waterfall-style profit structure chart with 4 bars: Profit, Loss, Fees, Net Profit.
 * Each bar is drawn as a floating bar [start, end] so steps appear sequentially.
 * @param {string} id - canvas element id
 * @param {Object|Array} structure - either the cumulative structure object or fallback to data array
 * Expected structure keys (best effort): profit, loss, fees, net_profit OR total_profit, total_loss, total_fees, net_profit
 */
function loadAccountProfitStructureCharts(id, structure) {
  const ctx = document.getElementById(id);
  if (!ctx) return null;

  // Normalize input
  let s = structure || {};
  if (Array.isArray(structure) && structure.length > 0) {
    // try to pick last entry if given whole timeseries
    s = structure[structure.length - 1] || {};
  }

  const profit = parseFloat(s.gross_profit) || 0;
  const loss = Math.abs(parseFloat(s.gross_loss)) || 0;
  const fees = Math.abs(parseFloat(s.fees)) || 0;
  const net = parseFloat(s.net_profit) || 0;

  // Cumulative positions for floating bars
  const start0 = 0;
  const end0 = profit;
  const start1 = end0;
  const end1 = end0 - loss;
  const start2 = end1;
  const end2 = end1 - fees;
  const start3 = 0; // draw net profit from zero to final net value
  const end3 = net;

  // Floating bar data format: y: [min, max]
  const labels = ["Profit", "Loss", "Fees", "Net Profit"];
  const values = [
    [start0, end0],
    [start1, end1],
    [start2, end2],
    [start3, end3],
  ];

  // Colors
  const profitColor = getCssVariableColor("--color-profit");
  const lossColor = getCssVariableColor("--color-loss");
  const feeColor = getCssVariableColor("--color-text", 0.6);
  const netColor = getCssVariableColor("--color-primary");
  const bgColors = [profitColor, lossColor, feeColor, netColor];

  // Destroy existing
  const existing = Chart.getChart(id);
  if (existing) existing.destroy();

  // Build dataset as objects so each item can have its own color
  const data = labels.map((lbl, i) => ({ x: lbl, y: values[i] }));
  // Plugin: draw a dashed horizontal line at y=0 (zero baseline)
  const zeroLinePlugin = {
    id: "zeroLine",
    afterDraw: (chart) => {
      const yScale = chart.scales?.y;
      if (!yScale) return;
      const yPixel = yScale.getPixelForValue(0);
      // Only draw if zero is within the chart area
      if (yPixel < chart.chartArea.top || yPixel > chart.chartArea.bottom)
        return;
      const { ctx } = chart;
      ctx.save();
      ctx.beginPath();
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = getCssVariableColor("--color-text", 0.25);
      ctx.lineWidth = 1;
      ctx.moveTo(chart.chartArea.left, yPixel + 0.5);
      ctx.lineTo(chart.chartArea.right, yPixel + 0.5);
      ctx.stroke();
      ctx.restore();
    },
  };

  const chart = new Chart(ctx.getContext("2d"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Structure",
          data: data,
          backgroundColor: bgColors,
          borderColor: bgColors,
          borderWidth: 1,
          borderRadius: 4,
          borderSkipped: false,
          barPercentage: 0.6,
          categoryPercentage: 0.6,
        },
      ],
    },
    options: getChartOptions(
      {
        title: (tooltipItems) => {
          // Use the label (category) as title
          return tooltipItems[0].label || "";
        },
        label: (tooltipItem) => {
          // tooltipItem.raw.y is [start, end]
          const pair = tooltipItem.raw?.y || [0, 0];
          const start = Number(pair[0]);
          const end = Number(pair[1]);
          const change = end - start;
          const sign = change >= 0 ? "+" : "";
          // Show start, end and change on separate lines
          return [`${sign}${formatNumber(change)}`];
        },
      },
      false,
      true
    ),
    plugins: [zeroLinePlugin],
  });

  return chart;
}

// Helper to format numbers consistently (adds fixed 2 decimals and thousands separator)
function formatNumber(n) {
  if (n === null || n === undefined || isNaN(n)) return "0";
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Creates a radar chart for comparing two datasets (e.g., Buy vs Sell)
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} options - Configuration object
 * @param {string} options.bgColor -
 * @param {string} options.textColor -
 * @param {string[]} options.labels - Array of labels for each axis
 * @param {Object[]} options.datasets - First dataset config { label, data, color }
 * @returns {Chart|null} - The Chart instance or null if canvas not found
 */
function loadRadarChart(canvasId, options) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const existingChart = Chart.getChart(canvasId);
  if (existingChart) existingChart.destroy();

  return new Chart(ctx, {
    type: "radar",
    data: {
      labels: options.labels,
      datasets: options.datasets.map((data, i) => {
        return {
          label: data.label,
          data: data.data,
          backgroundColor: data.bgColor,
          borderColor: data.color,
          borderWidth: 2,
          pointBackgroundColor: data.color,
          pointBorderColor: data.color,
          pointRadius: 4,
        };
      }),
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: 0,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: getCssVariableColor("--color-background"),
          titleColor: getCssVariableColor("--color-title"),
          bodyColor: getCssVariableColor("--color-text"),
          padding: 12,
          cornerRadius: 8,
          displayColors: false,
        },
      },
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: options.bgColor },
          angleLines: { color: options.bgColor },
          pointLabels: {
            color: options.textColor,
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
 * Build a radar chart from a performance data object.
 * Expected shape (performance entry from `get_performance_currencies`):
 * {
 *   profit, buy_profit, sell_profit,
 *   fees, buy_fees, sell_fees,
 *   net_profit, buy_net_profit, sell_net_profit,
 *   trades, winning_trades, losing_trades,
 *   buy_trades, buy_winning_trades, buy_losing_trades,
 *   sell_trades, sell_winning_trades, sell_losing_trades,
 *   ...
 * }
 */
function loadPerformanceRadarChart(canvasId, perf) {
  if (!perf) return null;

  const labels = ["Total", "Buy", "Sell"];

  const profitVals = [
    Number(perf.profit ?? 0),
    Number(perf.buy_profit ?? 0),
    Number(perf.sell_profit ?? 0),
  ];

  const netVals = [
    Number(perf.net_profit ?? 0),
    Number(perf.buy_net_profit ?? 0),
    Number(perf.sell_net_profit ?? 0),
  ];

  const feeVals = [
    Number(perf.fees),
    Number(perf.buy_fees ?? 0),
    Number(perf.sell_fees ?? 0),
  ];

  // Compute win rates as percentages if possible
  const totalWinRate =
    perf.winning_trades && perf.trades
      ? (perf.winning_trades / perf.trades) * 100
      : perf.win_rate ?? 0;
  const buyWinRate =
    perf.buy_winning_trades && perf.buy_trades
      ? (perf.buy_winning_trades / perf.buy_trades) * 100
      : perf.buy_win_rate ?? 0;
  const sellWinRate =
    perf.sell_winning_trades && perf.sell_trades
      ? (perf.sell_winning_trades / perf.sell_trades) * 100
      : perf.sell_win_rate ?? 0;
  const winRateVals = [
    Number(totalWinRate),
    Number(buyWinRate),
    Number(sellWinRate),
  ];

  // Use contrasting colors: profit (primary green), fees (muted), win rate (accent)
  let bgColor = getCssVariableColor("--color-profit");
  let textColor = getCssVariableColor("--color-profit");

  if (perf.fees > perf.profit) {
    bgColor = getCssVariableColor("--color-text", 0.8);
    textColor = getCssVariableColor("--color-text");
  }

  const profitColor = getCssVariableColor("--color-profit");
  const bgProfitColor = getCssVariableColor("--color-profit", 0.4);
  const feeColor = getCssVariableColor("--color-text");
  const bgFeeColor = getCssVariableColor("--color-text", 0.4);
  const netColor = getCssVariableColor("--color-primary");
  const bgNetColor = getCssVariableColor("--color-primary", 0.4);
  const winColor = getCssVariableColor("--color-primary");

  // Build and render radar with three datasets: Profit, Fees, WinRate (scaled)
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const existing = Chart.getChart(canvasId);
  if (existing) existing.destroy();

  return loadRadarChart(canvasId, {
    labels: labels,
    bgColor: bgColor,
    textColor: textColor,
    datasets: [
      {
        label: "Profit",
        data: profitVals,
        color: profitColor,
        bgColor: bgProfitColor,
      },
      {
        label: "Fees",
        data: feeVals,
        color: feeColor,
        bgColor: bgFeeColor,
      },
      {
        label: "Net profit",
        data: netVals,
        color: netColor,
        bgColor: bgNetColor,
      },
    ],
    // extra dataset for win rate rendered by calling loadRadarChart twice is not supported,
    // so we'll overlay win rate by creating a third dataset directly here using Chart API.
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
