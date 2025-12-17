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
          borderWidth: 1,
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
    options: {
      animation: false,
      responsive: true,
      layout: {
        padding: 0,
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          enabled: true,
          displayColors: false,
          backgroundColor: getCssVariableColor("--color-background"),
          titleColor: getCssVariableColor("--color-title"),
          bodyColor: getCssVariableColor("--color-text"),
          padding: 8,
          cornerRadius: 4,
          callbacks: {
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
          },
        },
      },
      interaction: {
        mode: "nearest",
        intersect: false,
      },
      scales: {
        x: {
          display: false,
          grid: { display: false, drawBorder: false },
        },
        y: {
          min: minValue,
          display: false,
          grid: { display: false, drawBorder: false },
        },
      },
    },
  });
}

function loadAccountProfitCharts(id, data) {
  const ctx = document
    .getElementById("accountProfitChart-" + id)
    .getContext("2d");

  //   console.log("Loading chart with data:", data);

  labels = data.map((item) => item.date);
  profitData = data.map((item) => item.profit);

  const series = {
    date: labels,
    profit: profitData,
    dailyProfit: data.map((item) => item.daily_profit),
  };

  const existingChart = Chart.getChart("accountProfitChart-" + id);
  if (existingChart) {
    existingChart.destroy();
  }

  new Chart(ctx, {
    type: "line",
    data: {
      labels: series.date,
      datasets: [
        {
          data: series.profit,
          borderWidth: 1,
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
          enabled: true,
          displayColors: false,
          backgroundColor: getCssVariableColor("--color-background"),
          titleColor: getCssVariableColor("--color-title"),
          bodyColor: getCssVariableColor("--color-text"),
          padding: 8,
          cornerRadius: 4,
          callbacks: {
            title: (tooltipItems) => {
              return tooltipItems[0].label;
            },
            label: (tooltipItem) => {
              const profit = `Profit: ${tooltipItem.formattedValue}`;
              const dailyProfit = `Daily Profit: ${
                series.dailyProfit[tooltipItem.dataIndex]
              }`;
              return [profit, dailyProfit];
            },
          },
        },
      },
      interaction: {
        mode: "nearest",
        intersect: false,
      },
      scales: {
        x: {
          display: false,
          grid: { display: false, drawBorder: false },
        },
        y: {
          display: false,
          grid: { display: false, drawBorder: false },
        },
      },
    },
  });
}
