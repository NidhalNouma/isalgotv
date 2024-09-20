console.log("js loaded");
function swapDivBtn(id1, id2) {
  const btn1 = document.getElementById(id1 + "-btn");
  const btn2 = document.getElementById(id2 + "-btn");
  const div1 = document.getElementById(id1);
  const div2 = document.getElementById(id2);

  const btnClass1 = btn1.classList.toString(); // Convert class list to string
  const btnClass2 = btn2.classList.toString(); // Convert class list to string

  btnClass1.split(" ").forEach((className) => {
    if (className) btn1?.classList.remove(className);
  });

  btnClass2.split(" ").forEach((className) => {
    if (className) btn2?.classList.remove(className);
  });

  btnClass1.split(" ").forEach((className) => {
    if (className) btn2?.classList.add(className);
  });

  btnClass2.split(" ").forEach((className) => {
    if (className) btn1?.classList.add(className);
  });

  div1.classList.add("hidden");
  div2.classList.remove("hidden");
}

function openLoader(title, id = "-pay-submit-", className = "block") {
  let spinner = document.getElementById("spinner" + id + title);
  if (spinner) spinner.style.display = className;
  let btn = document.getElementById("btn" + id + title);
  if (btn) btn.style.display = "none";

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";
}
function closeLoader(title, id = "-pay-submit-", className = "block") {
  let spinner = document.getElementById("spinner" + id + title);
  if (spinner) spinner.style.display = "none";
  let btn = document.getElementById("btn" + id + title);
  if (btn) btn.style.display = className;

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";
}

function changeHidden(id1, id2, className) {
  document.getElementById(id1)?.classList?.remove("hidden");
  document.getElementById(id2)?.classList?.add("hidden");

  if (className) {
    document.getElementById(id1)?.classList?.add(className);
    document.getElementById(id2)?.classList?.remove(className);
  }
}

function customDropdownBtnClick(newValue, textId, inputId, buttonId) {
  const text = document.getElementById(textId);
  const input = document.getElementById(inputId);
  const btn = document.getElementById(buttonId);
  if (text) text.innerText = newValue;
  if (input) input.value = newValue;
  if (btn) btn.click();
}

function validateNumberInput(input, maxLength) {
  let value = input.value.replace(/\D/g, "").slice(0, maxLength);

  let formattedValue = "";

  for (let i = 0; i < value.length; i++) {
    if (i > 0 && i % 4 === 0) {
      formattedValue += " ";
    }
    formattedValue += value[i];
  }

  input.value = formattedValue.trim();
}

let stripe, cardElement, elements;

function mountStripeElement(id) {
  const lbl = document.getElementById("lbl-card-element-" + id);
  if (!stripe) {
    // const stripe_key = document
    //   .getElementById("contextData")
    //   .getAttribute("stripe_public_key");
    stripe = Stripe(stripe_public_key);
  }

  let color = "#fff";
  if (lbl) {
    color = lbl.style.color;
    let style = window.getComputedStyle(lbl);
    color = style.getPropertyValue("color");
  }

  elements = stripe.elements();
  cardElement = elements.create("card", {
    hidePostalCode: true,
    disableLink: true,
    style: {
      base: {
        color: color,
        "font-family": "lato",
        "font-size": "0.875rem",
        "line-height": "1.25rem",

        iconColor: "rgb(156 163 175)",
        "::placeholder": {
          color: "rgb(156 163 175)",
        },
        ":focus": {
          "border-color": "hsl(229, 76%, 72%);",
        },
      },
    },
  });

  cardElement.mount("#card-element-" + id);
}

function unmountStripeElement(title) {
  if (cardElement) cardElement.unmount();
  closeLoader(title);
}

function paymentMethodSelected(pmId, inputId) {
  const pmValue = document.getElementById(inputId);

  document
    .getElementById("span-" + pmValue.value + "-" + inputId)
    ?.classList?.add("hidden");
  document
    .getElementById("span-" + pmId + "-" + inputId)
    ?.classList?.remove("hidden");

  pmValue.value = pmId;
}

async function onPayFormStripeSubmit(title) {
  openLoader(title, "-pay-submit-", "flex");
  const nameInput = document.getElementById("cardName-" + title);

  const pmValue = document.getElementById("pm-" + title);

  const paymentsList = document.getElementById("payment-card-list-" + title);
  console.log("Checking card for " + title + " ... " + pmValue.value);

  const errorDiv = document.getElementById("stripe-error-" + title);
  if (errorDiv) errorDiv.innerHTML = "";

  if (
    pmValue.value.length === 0 ||
    pmValue.value === "None" ||
    (paymentsList && paymentsList.classList.contains("hidden"))
  ) {
    const result = await stripe.createPaymentMethod({
      elements,
      params: {
        billing_details: {
          name: nameInput.value,
        },
      },
    });
    if (result.error) {
      let errorMsg = result.error.message + "\nNo payment method found!";
      let errorHtml = `<div class="mx-auto text-sm flex p-4 text-red-600 bg-red-800/10  rounded {{class}}" role="alert"><svg class="flex-shrink-0 inline w-4 h-4 me-3 mt-[2px]" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/></svg><span class="sr-only">Error!</span><div><p>${errorMsg}</p></div>`;
      if (errorDiv) errorDiv.innerHTML = errorHtml;
      closeLoader(title);
      return false;
    } else {
      pmValue.value = result.paymentMethod.id;
    }
  }

  let form = document.getElementById("form-pay-" + title);
  form.dispatchEvent(new Event("submit"));

  // closeLoader(title);
  return true;
}

//Hide css element after fadeout
function hideAll_hideMe() {
  const elements = document.querySelectorAll(".hideMe");
  // console.log("running", elements);

  elements.forEach(function (element) {
    element.addEventListener("animationend", function () {
      element.classList.add("hidden");
      // console.log(element);
    });
  });
}

hideAll_hideMe();

// Show/Hide replies

function toggleReplies(id) {
  const replies = document.getElementById("replies-" + id);
  const upArrow = document.getElementById("up-arrow-replies-" + id);
  const dnArrow = document.getElementById("down-arrow-replies-" + id);
  if (replies.classList.contains("hidden")) {
    replies.classList.remove("hidden");
    upArrow.classList.remove("hidden");
    dnArrow.classList.add("hidden");
  } else {
    replies.classList.add("hidden");
    dnArrow.classList.remove("hidden");
    upArrow.classList.add("hidden");
  }
}

function toggleForm(btnId, formId, textFocus = true) {
  const btn = document.getElementById(btnId);
  const form = document.getElementById(formId);
  if (btn && form)
    if (form.classList.contains("hidden")) {
      form.classList.remove("hidden");
      btn.classList.add("hidden");

      if (textFocus) {
        let firstTextField = form.querySelector("textarea");
        if (firstTextField) {
          firstTextField.focus();
        }
      }
    } else {
      form.classList.add("hidden");
      btn.classList.remove("hidden");
    }
}

function showSelectImgs(id) {
  const input = document.getElementById(id);
  input.click();
}

function showModalImages(images, imgId, id = "modal-images") {
  // console.log(images);
  const modal = document.getElementById(id);
  modal.classList.remove("hidden");

  let currentIndex = 0;

  const showImage = (index) => {
    const carouselItems = carouselContainer.querySelectorAll(
      "[data-carousel-item]"
    );
    carouselItems.forEach((item, i) => {
      item.style.display = i === index ? "block" : "none";
    });

    currentIndex = index;
  };

  document
    .getElementById("prev-button-carousel")
    .addEventListener("click", () => {
      currentIndex = (currentIndex - 1 + images.length) % images.length;
      showImage(currentIndex);
    });

  document
    .getElementById("next-button-carousel")
    .addEventListener("click", () => {
      currentIndex = (currentIndex + 1) % images.length;
      showImage(currentIndex);
    });

  const carouselControl = document.getElementById("controls-carousel");
  const carouselContainer = document.getElementById("images-carousel");
  while (carouselContainer.firstChild) {
    carouselContainer.removeChild(carouselContainer.firstChild);
  }

  images.forEach((img, index) => {
    console.log(img);
    const imgElement = document.createElement("img");
    imgElement.src = img.imageUrl;
    imgElement.classList.add(
      "object-scale-down",
      "absolute",
      "max-w-[95%]",
      "max-h-[99%]",
      "aspect-auto",
      "block",
      "-translate-x-1/2",
      "-translate-y-1/2",
      "top-1/2",
      "left-1/2"
    );

    const carouselItem = document.createElement("div");
    carouselItem.classList.add("hidden", "duration-700", "ease-in-out");
    carouselItem.setAttribute("data-carousel-item", "");
    carouselItem.appendChild(imgElement);

    carouselContainer.appendChild(carouselItem);

    if (img.id == imgId) {
      showImage(index);
    }
  });
}

htmx.on("htmx:afterRequest", (evt) => {
  if (evt?.detail?.target.id === "resultsDiv") {
    clearResultForm();
  }

  if (evt?.detail?.target.id.includes("form-pay-")) {
    const title = evt?.detail?.target.id.replace("form-pay-", "");
    mountStripeElement(title);

    const pmValue = document.getElementById("pm-" + title);
    if (pmValue) pmValue.value = "None";
  }

  if (evt?.detail?.target.id.includes("stripe-error-")) {
    const title = evt?.detail?.target.id.replace("stripe-error-", "");
    closeLoader(title);

    const pmValue = document.getElementById("pm-" + title);
    if (pmValue) {
      const id1 = "payment-card-list-" + title;
      if (document.getElementById(id1)?.classList?.contains("hidden")) {
        pmValue.value = "None";
      }
    }
  }

  if (evt?.detail?.target.id.includes("stripe-next-")) {
    console.log("next ...");
    const title = evt?.detail?.target.id.replace("stripe-next-", "");
    closeLoader(title);

    changeHidden("submit-btn-sub-" + title, "submit-btn-next-" + title, "flex");

    const pmValue = document.getElementById("pm-" + title);
    if (pmValue) {
      const id1 = "payment-card-list-" + title;
      if (document.getElementById(id1)?.classList?.contains("hidden")) {
        pmValue.value = "None";
      }
    }
  }

  if (evt?.detail?.target.id === "setting-payment_methods") {
    let title = "payment_methods";
    const closeForm = document.getElementById(
      "add-payment_methods-close-form-btn"
    );
    closeForm.click();

    const pmValue = document.getElementById("pm-" + title);
    if (pmValue) pmValue.value = "None";
  }

  if (evt?.detail?.target.id.includes("tradingview_username_submit")) {
    closeLoader("", "-tv", "flex");
  }

  if (evt?.detail?.target.id.includes("contact_us_mail")) {
    closeLoader("-send-mail", "");
  }

  if (
    evt?.detail?.target.id.includes("add-comment-form-errors") ||
    evt?.detail?.target.id.includes("commentsDiv")
  ) {
    // const title = evt?.detail?.target.id.replace("stripe-error-", "");
    closeLoader("", "-add-comment", "inline-flex");
  }

  if (evt?.detail?.target.id.includes("reply-form-errors-")) {
    const title = evt?.detail?.target.id.replace("reply-form-errors-", "");

    closeLoader(title, "-add-reply-", "inline-flex");
  }

  if (evt?.detail?.target.id.includes("replies-")) {
    const title = evt?.detail?.target.id.replace("replies-", "");

    closeLoader(title, "-add-reply-", "inline-flex");
  }

  if (evt?.detail?.target.id.includes("access-mb")) {
    openModel("get-access-modal");
  }
});

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
      resultElement.classList.add("brightness-125");
      resultElement.classList.add("transition");
      resultElement.classList.add("ease-in-out");
      resultElement.classList.add("duration-1000");

      // Remove the highlight after a certain time (e.g., 3 seconds)
      setTimeout(() => {
        resultElement.classList.remove("brightness-125");
        // resultElement.classList.remove("transition");
        // resultElement.classList.remove("ease-in-out");
        // resultElement.classList.remove("duration-1000");
      }, 3000);
    }
  }
}

function handleSettingCsvFileSelect(event) {
  const fileInput = event.target;
  const file = fileInput.files[0];

  if (!file) {
    return;
  }

  const reader = new FileReader();

  reader.onload = function (e) {
    const contents = e.target.result;
    const lines = contents.split("\n");

    let previousKey = "";
    let startKey = "";
    let cnt = 0;

    lines.forEach((line, index) => {
      let [key, value] = line.split(",");

      value = value.replace(/(\r\n|\n|\r)/gm, "");
      key = key.replace(/(\r\n|\n|\r)/gm, "");

      const originalKey = key;

      if (startKey) key = startKey;

      let keyNumber = key + "_" + cnt;

      const input = document.getElementById("id_settings_" + keyNumber);
      if (input) {
        cnt = cnt + 1;
        if (startKey === "") startKey = key;

        if (input.type == "checkbox") {
          if (value === "On") {
            input.checked = true;
            input.value = "true";
          } else {
            input.checked = false;
            input.value = "false";
          }
        } else if (input.type == "text") {
          const dropdown = document.getElementById(
            "dropdown_text_" + keyNumber
          );
          if (dropdown) dropdown.innerHTML = value;
          input.value = value;
        }
      } else {
        if (originalKey === "Symbol" && document.getElementById("pair")) {
          const [broker, symbol] = value.split(":");
          document.getElementById("pair").value = symbol;
          document.getElementById("broker").value = broker;
        } else if (originalKey === "Trading range") {
          const [start, end] = value.split(" — ");

          if (document.getElementById("start_at")) {
            const time = new Date(start);
            time.setMinutes(time.getMinutes() - time.getTimezoneOffset());
            document.getElementById("start_at").value = time
              .toISOString()
              .slice(0, 16);
          }
          if (document.getElementById("end_at")) {
            const time = new Date(end);
            time.setMinutes(time.getMinutes() - time.getTimezoneOffset());
            document.getElementById("end_at").value = time
              .toISOString()
              .slice(0, 16);
          }
        } else if (originalKey === "Timeframe") {
          const [num, str] = value.split(" ");

          if (document.getElementById("time_frame"))
            document.getElementById("time_frame").value = num;
          if (document.getElementById("time_frame_period")) {
            let val = str.replace(/(\r\n|\n|\r)/gm, "");

            if (val.toLowerCase().indexOf("second") !== -1) val = "seconds";
            else if (val.toLowerCase().indexOf("minute") !== -1)
              val = "minutes";
            else if (val.toLowerCase().indexOf("hour") !== -1) val = "hours";
            else if (val.toLowerCase().indexOf("day") !== -1) val = "days";
            else if (val.toLowerCase().indexOf("week") !== -1) val = "weeks";
            else if (val.toLowerCase().indexOf("month") !== -1) val = "months";
            else if (val.toLowerCase().indexOf("year") !== -1) val = "years";

            document.getElementById("time_frame_period").value = val;
          }
        } else if (originalKey === "Initial capital") {
          if (document.getElementById("initial_capital"))
            document.getElementById("initial_capital").value = value;
        }
      }

      previousKey = key;
    });

    fileInput.value = null;
  };

  reader.readAsText(file);
}

function handleResultsCsvFileSelect(event) {
  const fileInput = event.target;
  const file = fileInput.files[0];

  if (!file) {
    return;
  }

  const reader = new FileReader();

  reader.onload = function (e) {
    const contents = e.target.result;
    const lines = contents.split("\n");

    let previousKey = "";
    lines.forEach((line, index) => {
      let [key, allUSD, allPerc, longUSD, longPerc, shortUSD, shortPerc] =
        line.split(",");

      key = key.replace(/(\r\n|\n|\r)/gm, "");
      allUSD = allUSD.replace(/(\r\n|\n|\r)/gm, "");
      allPerc = allPerc.replace(/(\r\n|\n|\r)/gm, "");
      longUSD = longUSD.replace(/(\r\n|\n|\r)/gm, "");
      longPerc = longPerc.replace(/(\r\n|\n|\r)/gm, "");
      shortUSD = shortUSD.replace(/(\r\n|\n|\r)/gm, "");
      shortPerc = shortPerc.replace(/(\r\n|\n|\r)/gm, "");

      if (key === "Net Profit") {
        if (document.getElementById("net_profit"))
          document.getElementById("net_profit").value = allUSD;
        if (document.getElementById("net_profit_long"))
          document.getElementById("net_profit_long").value = longUSD;
        if (document.getElementById("net_profit_short"))
          document.getElementById("net_profit_short").value = shortUSD;
        if (document.getElementById("net_profit_percentage"))
          document.getElementById("net_profit_percentage").value = allPerc;
        if (document.getElementById("net_profit_percentage_long"))
          document.getElementById("net_profit_percentage_long").value =
            longPerc;
        if (document.getElementById("net_profit_percentage_short"))
          document.getElementById("net_profit_percentage_short").value =
            shortPerc;
      } else if (key === "Gross Profit") {
        if (document.getElementById("gross_profit"))
          document.getElementById("gross_profit").value = allUSD;
        if (document.getElementById("gross_profit_long"))
          document.getElementById("gross_profit_long").value = longUSD;
        if (document.getElementById("gross_profit_short"))
          document.getElementById("gross_profit_short").value = shortUSD;
        if (document.getElementById("gross_profit_percent"))
          document.getElementById("gross_profit_percent").value = allPerc;
        if (document.getElementById("gross_profit_percent_long"))
          document.getElementById("gross_profit_percent_long").value = longPerc;
        if (document.getElementById("gross_profit_percent_short"))
          document.getElementById("gross_profit_percent_short").value =
            shortPerc;
      } else if (key === "Gross Loss") {
        if (document.getElementById("gross_loss"))
          document.getElementById("gross_loss").value = allUSD;
        if (document.getElementById("gross_loss_long"))
          document.getElementById("gross_loss_long").value = longUSD;
        if (document.getElementById("gross_loss_short"))
          document.getElementById("gross_loss_short").value = shortUSD;
        if (document.getElementById("gross_loss_percent"))
          document.getElementById("gross_loss_percent").value = allPerc;
        if (document.getElementById("gross_loss_percent_long"))
          document.getElementById("gross_loss_percent_long").value = longPerc;
        if (document.getElementById("gross_loss_percent_short"))
          document.getElementById("gross_loss_percent_short").value = shortPerc;
      } else if (key === "Profit Factor") {
        if (document.getElementById("profit_factor"))
          document.getElementById("profit_factor").value = allUSD;
        if (document.getElementById("profit_factor_long"))
          document.getElementById("profit_factor_long").value = longUSD;
        if (document.getElementById("profit_factor_short"))
          document.getElementById("profit_factor_short").value = shortUSD;
      } else if (key === "Percent Profitable") {
        if (document.getElementById("profitable_percentage"))
          document.getElementById("profitable_percentage").value = allUSD;
        if (document.getElementById("profitable_percentage_long"))
          document.getElementById("profitable_percentage_long").value = longUSD;
        if (document.getElementById("profitable_percentage_short"))
          document.getElementById("profitable_percentage_short").value =
            shortUSD;
      } else if (key === "Max Drawdown") {
        if (document.getElementById("max_dd"))
          document.getElementById("max_dd").value = allUSD;
        if (document.getElementById("max_dd_percentage"))
          document.getElementById("max_dd_percentage").value = allPerc;
      } else if (key === "Total Closed Trades") {
        if (document.getElementById("total_trades"))
          document.getElementById("total_trades").value = allUSD;
        if (document.getElementById("total_trades_long"))
          document.getElementById("total_trades_long").value = longUSD;
        if (document.getElementById("total_trades_short"))
          document.getElementById("total_trades_short").value = shortUSD;
      } else if (key === "Number Winning Trades") {
        if (document.getElementById("winning_trades"))
          document.getElementById("winning_trades").value = allUSD;
        if (document.getElementById("winning_trades_long"))
          document.getElementById("winning_trades_long").value = longUSD;
        if (document.getElementById("winning_trades_short"))
          document.getElementById("winning_trades_short").value = shortUSD;
      } else if (key === "Number Losing Trades") {
        if (document.getElementById("losing_trades"))
          document.getElementById("losing_trades").value = allUSD;
        if (document.getElementById("losing_trades_long"))
          document.getElementById("losing_trades_long").value = longUSD;
        if (document.getElementById("losing_trades_short"))
          document.getElementById("losing_trades_short").value = shortUSD;
      }
    });

    fileInput.value = null;
  };

  reader.readAsText(file);
}

function getNumberOfLines(id) {
  const element = document.getElementById(id);
  let lineHeight = parseFloat(window.getComputedStyle(element).lineHeight);
  let totalHeight = element.scrollHeight;
  // console.log(totalHeight, totalHeight / lineHeight);
  return Math.round(totalHeight / lineHeight);
}

const modals = {};
function openModel(id) {
  const modalElement = document.querySelector("#" + id);

  const modalOptions = {
    bodyScrolling: false,

    bodyScrolling: true,
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
    },
    // placement: "bottom-right",
    // backdrop: "dynamic",
    // backdropClasses: "bg-gray-900/50 dark:bg-gray-900/80 fixed inset-0 z-40",
    // onHide: () => {
    //   console.log("modal is hidden");
    // },
    // onShow: () => {
    //   console.log("modal is shown");
    // },
    // onToggle: () => {
    //   console.log("modal has been toggled");
    // },
  };

  // TODO: Fix modal problem after htmx response when cancel a membership
  if (modals[id]) modals[id].show();
  else {
    const modal = new Modal(modalElement, modalOptions);
    modals[id] = modal;
    modal.show();
  }

  document.querySelector("html").style.overflowY = "hidden";
}

function hideModel(id) {
  if (modals[id]) modals[id].hide();
}

const drawers = {};
function openDrawer(id) {
  const draweli = document.querySelector("#" + id);

  const drawerOptions = {
    placement: "right",

    backdrop: true,
    bodyScrolling: true,

    // backdrop: "dynamic",
    // backdropClasses: "bg-text/80 ",
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
    },
    // onShow: () => {
    //   console.log("modal is shown");
    // },
    // onToggle: () => {
    //   console.log("modal has been toggled");
    // },
  };

  if (drawers[id]) drawers[id].show();
  else {
    const drawer = new Drawer(draweli, drawerOptions);
    drawers[id] = drawer;
    drawer.show();
  }

  document.querySelector("html").style.overflowY = "hidden";
}

function hideDrawer(id) {
  if (drawers[id]) drawers[id].hide();
}

function openPopupWindow(url, name = "windowChart") {
  const h = (window.screen.height * 80) / 100;
  const w = (window.screen.width * 80) / 100;

  const Y =
    window.outerHeight / 2 - h / 2; /* 0.5 * windowHeight - 0.5 * popupHeight */
  const X =
    window.outerWidth / 2 - w / 2; /* 0.5 * windowWidth - 0.5 * popupWidth */

  window.open(url, name, `width=${w},${h}=600,top=${Y},left=${X}`);
  return false;
}

function showSelectedFiles(inputId, listId) {
  const input = document.getElementById(inputId);
  const fileList = document.getElementById(listId);
  fileList.innerHTML = ""; // Clear existing list

  for (var i = 0; i < input.files.length; i++) {
    let file = input.files[i];
    let fileReader = new FileReader();

    let fileSize = (file.size / 1024).toFixed(2); // Convert size to KB
    let fileSizeDisplay =
      fileSize > 1024 ? (fileSize / 1024).toFixed(2) + " MB" : fileSize + " KB";

    let fileName = file.name;

    // Closure to capture the file information.
    fileReader.onload = (function (theFile) {
      return function (e) {
        var mainDiv = document.createElement("div");
        mainDiv.className =
          "flex justify-between items-center mt-4 mb-1 bg-text/30 text-text text-sm rounded-md p-2 max-w-full";

        let imgDiv = document.createElement("div");
        imgDiv.className = "flex items-center grow-0 max-w-[min(20rem,80%)]";

        if (theFile.type.match("image.*")) {
          let img = new Image();
          img.src = e.target.result;
          img.className = "h-16 w-16 mr-3 rounded-lg";
          imgDiv.appendChild(img);
        } else if (theFile.type.match("video.*")) {
          let video = document.createElement("video");
          video.src = e.target.result;
          video.className = "h-16 w-16 mr-3 rounded-lg";
          video.controls = false;
          imgDiv.appendChild(video);
        } else {
          imgDiv.innerHTML =
            '<div class="w-16 aspect-square p-2 flex items-center justify-center"><svg class="h-8 w-8 fill-text p-1 " stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 384 512" xmlns="http://www.w3.org/2000/svg"><path d="M64 464c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16H224v80c0 17.7 14.3 32 32 32h80V448c0 8.8-7.2 16-16 16H64zM64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V154.5c0-17-6.7-33.3-18.7-45.3L274.7 18.7C262.7 6.7 246.5 0 229.5 0H64zm56 256c-13.3 0-24 10.7-24 24s10.7 24 24 24H264c13.3 0 24-10.7 24-24s-10.7-24-24-24H120zm0 96c-13.3 0-24 10.7-24 24s10.7 24 24 24H264c13.3 0 24-10.7 24-24s-10.7-24-24-24H120z"></path></svg></div>';
        }

        var hTitle = document.createElement("h6");
        var hSize = document.createElement("h6");

        hTitle.textContent = fileName;
        hTitle.className = "line-clamp-1";
        hSize.textContent = fileSizeDisplay;
        hSize.className = "text-text/80 text-xs line-clamp-1 ";

        let textDiv = document.createElement("div");
        textDiv.appendChild(hTitle);
        textDiv.appendChild(hSize);

        imgDiv.appendChild(textDiv);
        mainDiv.appendChild(imgDiv);

        fileList.appendChild(mainDiv);
      };
    })(file);

    // Read in the image file as a data URL.
    fileReader.readAsDataURL(file);
  }
}
