function scrollToResultOrComment(type, id) {
  let resultElement = document.getElementById(`${type}-${id}`);
  if (!id) resultElement = document.getElementById(`${type}`);

  if (resultElement) {
    // Calculate the scroll position to center the element
    const windowHeight = window.innerHeight;
    const elementTop = resultElement.getBoundingClientRect().top;
    const offset = elementTop - windowHeight / 2;

    // Scroll to the element
    window.scrollTo({
      top: window.scrollY + offset,
      behavior: "smooth",
    });

    if (id) {
      // Add a highlight class
      resultElement.classList.add("bg-text/10");
      resultElement.classList.add("transition-all");
      resultElement.classList.add("ease-in-out");
      resultElement.classList.add("duration-250");
      resultElement.classList.add("rounded-lg");

      // Remove the highlight after a certain time (e.g., 3 seconds)
      setTimeout(() => {
        resultElement.classList.remove("bg-text/10");
        // resultElement.classList.remove("transition");
        // resultElement.classList.remove("ease-in-out");
        // resultElement.classList.remove("duration-1000");
      }, 1000);
    }
  }
}

function handleXlsxFileSelect(event) {
  const fileInput = event.target;
  const file = fileInput.files[0];

  if (!file) {
    return;
  }

  const reader = new FileReader();

  reader.onload = function (e) {
    const data = new Uint8Array(e.target.result);
    const workbook = XLSX.read(data, { type: "array" });

    // Process settings (Properties tab)
    if (workbook.Sheets["Properties"]) {
      const propertiesSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Properties"],
        { header: 1 },
      );
      fillSettingsFromSheet(propertiesSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Performance"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Performance"],
        { header: 1 },
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Trades analysis"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Trades analysis"],
        { header: 1 },
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Risk performance ratios"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Risk performance ratios"],
        { header: 1 },
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Risk-adjusted performance"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Risk-adjusted performance"],
        { header: 1 },
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["List of trades"]) {
      const listOfTrades = XLSX.utils.sheet_to_json(
        workbook.Sheets["List of trades"],
        { header: 1 },
      );
      // console.log("List of trades:", listOfTrades);

      if (document.getElementById("add-trades-list")) {
        const tradesTable = document.getElementById("add-trades-list");
        tradesTable.value = JSON.stringify(listOfTrades);
      }
    }

    fileInput.value = null;
  };

  reader.readAsArrayBuffer(file);
}

function fillSettingsFromSheet(sheetData) {
  let cnt = 0;
  let startKey = "";
  let prevKey = "";

  if (document.getElementById("initial_capital"))
    document.getElementById("initial_capital").value = "";

  sheetData.forEach((row) => {
    let [key, value] = row;

    key = key.toString().trim();
    value = value.toString().trim();

    let inputKey = key;
    if (startKey) inputKey = startKey;

    let keyNumber = inputKey + "_" + cnt;
    const input = document.getElementById("id_settings_" + keyNumber);

    if (input) {
      cnt++;
      if (!startKey) startKey = key;

      if (input.type == "checkbox") {
        if (value === "On") {
          input.checked = true;
          input.value = "true";
        } else {
          input.checked = false;
          input.value = "false";
        }
      } else if (input.type == "text") {
        const dropdown = document.getElementById("dropdown_text_" + keyNumber);
        if (dropdown) dropdown.innerHTML = value;
        input.value = value;
      }
    } else {
      // Handle special cases for specific settings
      if (key === "Symbol" && document.getElementById("pair")) {
        const [broker, symbol] = value.split(":");
        document.getElementById("pair").value = symbol;
        document.getElementById("broker").value = broker;
      } else if (key === "Trading range") {
        const [start, end] = value.split(" — ");
        if (document.getElementById("start_at")) {
          let time = new Date(start);
          time.setMinutes(time.getMinutes() - time.getTimezoneOffset());
          document.getElementById("start_at").value = time
            .toISOString()
            .slice(0, 16);
        }
        if (document.getElementById("end_at")) {
          let time = new Date(end);
          time.setMinutes(time.getMinutes() - time.getTimezoneOffset());
          document.getElementById("end_at").value = time
            .toISOString()
            .slice(0, 16);
        }
      } else if (key === "Timeframe" && prevKey === "Symbol") {
        const [num, period] = value.split(" ");
        document.getElementById("time_frame").value = num;
        document.getElementById("time_frame_period").value =
          convertTimeframePeriod(period);
      } else if (
        key === "Initial capital" &&
        document.getElementById("initial_capital")
      ) {
        document.getElementById("initial_capital").value =
          value + document.getElementById("initial_capital").value;
      } else if (
        key === "Currency" &&
        document.getElementById("initial_capital")
      ) {
        document.getElementById("initial_capital").value += " " + value;
      }
    }

    prevKey = key;
  });
}

function fillResultsFromSheet(sheetData) {
  sheetData.forEach((row) => {
    // console.log(row);
    let [key, allUSD, allPerc, longUSD, longPerc, shortUSD, shortPerc] =
      row.map((v) => (v ? v.toString().trim() : ""));

    key = key.toLowerCase();

    switch (key) {
      case "net profit":
        setResultValues(
          "net_profit",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "gross profit":
        setResultValues(
          "gross_profit",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "gross loss":
        setResultValues(
          "gross_loss",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "profit factor":
        setResultValues("profit_factor", allUSD, longUSD, shortUSD);
        break;
      case "percent profitable":
        setResultValues(
          "profitable_percentage",
          trimPercentage(allPerc),
          trimPercentage(longPerc),
          trimPercentage(shortPerc),
        );
        break;
      case "max equity drawdown":
      case "max equity drawdown (close-to-close)":
        document.getElementById("max_dd").value = allUSD;
        document.getElementById("max_dd_percentage").value =
          trimPercentage(allPerc);
        break;
      case "total trades":
        setResultValues("total_trades", allUSD, longUSD, shortUSD);
        break;
      case "winning trades":
        setResultValues("winning_trades", allUSD, longUSD, shortUSD);
        break;
      case "losing trades":
        setResultValues("losing_trades", allUSD, longUSD, shortUSD);
        break;
      case "avg p&l":
        setResultValues(
          "avg_trade",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "avg winning trade":
        setResultValues(
          "avg_winning_trade",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "avg losing trade":
        setResultValues(
          "avg_losing_trade",
          allUSD,
          longUSD,
          shortUSD,
          allPerc,
          longPerc,
          shortPerc,
        );
        break;
      case "ratio avg win / avg loss":
        setResultValues("ratio_trade", allUSD, longUSD, shortUSD);
        break;
    }
  });
}

// Helper function to set values
function setResultValues(
  baseKey,
  allUSD,
  longUSD,
  shortUSD,
  allPerc = "",
  longPerc = "",
  shortPerc = "",
) {
  if (document.getElementById(baseKey))
    document.getElementById(baseKey).value = allUSD;
  if (document.getElementById(baseKey + "_long"))
    document.getElementById(baseKey + "_long").value = longUSD;
  if (document.getElementById(baseKey + "_short"))
    document.getElementById(baseKey + "_short").value = shortUSD;
  if (document.getElementById(baseKey + "_percentage"))
    document.getElementById(baseKey + "_percentage").value =
      trimPercentage(allPerc);
  if (document.getElementById(baseKey + "_percentage_long"))
    document.getElementById(baseKey + "_percentage_long").value =
      trimPercentage(longPerc);
  if (document.getElementById(baseKey + "_percentage_short"))
    document.getElementById(baseKey + "_percentage_short").value =
      trimPercentage(shortPerc);
}

function trimPercentage(num) {
  num = parseFloat(num);

  return num.toFixed(2);
}

// Helper function to convert timeframe period
function convertTimeframePeriod(val) {
  if (!val) return val;
  val = val.toLowerCase();
  if (val.includes("second")) return "seconds";
  if (val.includes("minute")) return "minutes";
  if (val.includes("hour")) return "hours";
  if (val.includes("day")) return "days";
  if (val.includes("week")) return "weeks";
  if (val.includes("month")) return "months";
  if (val.includes("year")) return "years";
  return val;
}

function loadTradesData(result_id) {
  const rawDiv = document.getElementById("trades-data-" + result_id);
  if (!rawDiv) return;

  const raw = rawDiv.textContent;
  const data = JSON.parse(raw);
  const header = data[0];
  const rows = data.slice(1).reverse();
  const skipIndex = header.indexOf("Signal");
  const tradeIndex = header.indexOf("Trade #");
  const typeIndex = header.indexOf("Type");
  let dateIndex = header.indexOf("Date/time");
  if (dateIndex === -1) {
    console.warn("Could not find 'Date/time' column, trying 'Date and time'");
    dateIndex = header.indexOf("Date and time");
  }
  // console.log("Header:", header);
  // console.log("Type Index:", typeIndex);
  // console.log("Date Index:", dateIndex);
  // Dynamically find the price column (e.g., "Price USD", "Price EUR", etc.)
  const priceIndex = header.findIndex((text) => text.startsWith("Price "));

  const thead = document.getElementById("trades-header-" + result_id);
  thead.innerHTML = "";
  header.forEach((text, i) => {
    if (i === skipIndex) return;
    const th = document.createElement("th");
    th.className =
      "text-left px-4 py-2 text-xs text-text/60 font-medium truncate";
    th.textContent = text;
    thead.appendChild(th);
  });

  // Group rows by trade number
  const grouped = {};
  rows.forEach((row) => {
    const tradeNum = row[tradeIndex];
    grouped[tradeNum] = grouped[tradeNum] || [];
    grouped[tradeNum].push(row);
  });

  const tbody = document.getElementById("trades-body-" + result_id);
  tbody.innerHTML = "";

  Object.keys(grouped)
    .sort((a, b) => b - a)
    .forEach((tradeNum) => {
      const pair = grouped[tradeNum];
      if (pair.length < 2) return;
      const exitRow = pair[0];
      const entryRow = pair[1];
      const tr = document.createElement("tr");
      tr.classList.add("border-b", "border-text/10", "hover:bg-text/10");
      header.forEach((_, i) => {
        if (i === skipIndex) return;
        const td = document.createElement("td");
        td.className =
          "px-4 py-2 text-left truncate space-y-2 rounded-md text-xs";
        if (header[i].includes("Profit")) {
          if (exitRow[i] >= 0) td.classList.add("text-profit");
          else if (exitRow[i] < 0) td.classList.add("text-loss");
        }
        if (i === tradeIndex) {
          td.textContent = tradeNum;
        } else if (i === typeIndex || i === priceIndex) {
          // display exit then entry values on separate lines
          td.innerHTML = `<div>${entryRow[i]}</div><div>${exitRow[i]}</div>`;
        } else if (i === dateIndex) {
          // format both dates
          const formatDate = (cell) => {
            const d = new Date((cell - 25569) * 86400 * 1000);
            const datePart = d.toLocaleDateString("en-US", {
              year: "numeric",
              month: "short",
              day: "2-digit",
            });
            const timePart = d.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            });
            return `<div>${datePart}, ${timePart}</div>`;
          };
          td.innerHTML = formatDate(entryRow[i]) + formatDate(exitRow[i]);
        } else if (header[i].includes("%")) {
          // Multiply raw percentage by 100 and append '%' sign, showing exit then entry
          td.innerHTML = `${(exitRow[i] * 100).toFixed(2)}%`;
        } else {
          td.textContent = exitRow[i];
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
}
