console.log("js loaded");

// Helper to get CSRF token from cookies
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    document.cookie.split(";").forEach((cookie) => {
      const [key, val] = cookie.trim().split("=");
      if (key === name) {
        cookieValue = decodeURIComponent(val);
      }
    });
  }
  return cookieValue;
}

function copyText(text) {
  // Copy the text to clipboard
  navigator.clipboard
    .writeText(text)
    .then(() => {
      console.log("Text copied to clipboard: " + text);
    })
    .catch((err) => {
      console.error("Error copying text: ", err);
    });
}

function copyPlainText(id) {
  const codeElement = document.getElementById(id);

  // Get the plain text content (stripping all HTML tags)
  const text = codeElement.innerText.trim();

  // Copy the text to clipboard
  navigator.clipboard
    .writeText(text)
    .then(() => {
      console.log("Text copied to clipboard: " + text);
    })
    .catch((err) => {
      console.error("Error copying text: ", err);
    });
}

/**
 * Retrieves the CSS variable and returns it as a full HSL or color string.
 * @param {string} varName - CSS variable name (e.g. '--color-primary').
 * @returns {string} - Resolved color, e.g. 'hsl(227, 91%, 59%)' or '#3861f6'.
 */

/**
 * Retrieves the CSS variable and returns it as a full HSL or color string, optionally with alpha.
 * @param {string} varName - CSS variable name (e.g. '--color-primary').
 * @param {number|string} [alpha] - Optional alpha value (0-1).
 * @returns {string} - Resolved color, e.g. 'hsl(227, 91%, 59%)', '#3861f6', or with alpha if requested.
 */
function getCssVariableColor(varName, alpha) {
  const rootStyles = getComputedStyle(document.documentElement);
  let raw = rootStyles.getPropertyValue(varName);
  raw = raw.trim();

  // If hex color (e.g. #abc or #aabbcc)
  if (raw.startsWith("#")) {
    if (alpha !== undefined && alpha !== null) {
      // Expand shorthand hex (#abc) to full form (#aabbcc)
      let hex = raw.slice(1);
      if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
      }
      const r = parseInt(hex.substring(0, 2), 16);
      const g = parseInt(hex.substring(2, 4), 16);
      const b = parseInt(hex.substring(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    return raw;
  }

  // If rgb or rgba
  if (raw.startsWith("rgb(")) {
    if (alpha !== undefined && alpha !== null) {
      // Convert rgb to rgba by inserting alpha
      const rgbBody = raw.slice(4, -1);
      return `rgba(${rgbBody}, ${alpha})`;
    }
    return raw;
  }
  if (raw.startsWith("rgba(")) {
    // Already rgba, optionally override alpha if provided
    if (alpha !== undefined && alpha !== null) {
      const parts = raw.slice(5, -1).split(",");
      if (parts.length >= 3) {
        const [r, g, b] = parts;
        return `rgba(${r.trim()},${g.trim()},${b.trim()},${alpha})`;
      }
    }
    return raw;
  }

  // If hsl or hsla
  if (raw.startsWith("hsl(")) {
    if (alpha !== undefined && alpha !== null) {
      // Convert hsl to hsla
      const hslBody = raw.slice(4, -1);
      return `hsla(${hslBody}, ${alpha})`;
    }
    return raw;
  }
  if (raw.startsWith("hsla(")) {
    // Already hsla, optionally override alpha if provided
    if (alpha !== undefined && alpha !== null) {
      const parts = raw.slice(5, -1).split(",");
      if (parts.length >= 3) {
        const [h, s, l] = parts;
        return `hsla(${h.trim()},${s.trim()},${l.trim()},${alpha})`;
      }
    }
    return raw;
  }

  // Space-separated H S L parts (e.g. '227 91% 59%')
  const parts = raw.split(/\s+/);
  if (parts.length === 3) {
    const [h, s, l] = parts;
    if (alpha !== undefined && alpha !== null) {
      return `hsla(${h}, ${s}, ${l}, ${alpha})`;
    }
    return `hsl(${h}, ${s}, ${l})`;
  }

  return raw;
}

function toggleDropdown(dropdownId) {
  var dropdown = document.getElementById(dropdownId);

  if (dropdown.classList.contains("hidden")) {
    dropdown.classList.remove("hidden");
    dropdown.classList.add("block");
    var arrow = document.getElementById(dropdownId + "-arrow");
    if (arrow) {
      arrow.style.transform = "rotate(180deg)";
      function toggleDropdown(dropdownId) {
        var dropdown = document.getElementById(dropdownId);

        if (dropdown.classList.contains("hidden")) {
          dropdown.classList.remove("hidden");
          var arrow = document.getElementById(dropdownId + "-arrow");
          if (arrow) {
            arrow.style.transform = "rotate(180deg)";
          }
        } else {
          dropdown.classList.add("hidden");
          var arrow = document.getElementById(dropdownId + "-arrow");
          if (arrow) {
            arrow.style.transform = "rotate(0deg)";
          }
        }
      }
    }
  } else {
    dropdown.classList.add("hidden");
    dropdown.classList.remove("block");
    var arrow = document.getElementById(dropdownId + "-arrow");
    if (arrow) {
      arrow.style.transform = "rotate(0deg)";
    }
  }
}

function handleThreeSection(clickedButton, id1, id2, id3, btnClass) {
  let section1 = document.getElementById("section-" + id1);
  let section2 = document.getElementById("section-" + id2);
  let section3 = document.getElementById("section-" + id3);

  let btn1 = document.getElementById("btn-" + id1);
  let btn2 = document.getElementById("btn-" + id2);
  let btn3 = document.getElementById("btn-" + id3);

  // Reset all buttons and sections
  [btn1, btn2, btn3].forEach((btn) => btn.classList.remove(btnClass));
  [section1, section2, section3].forEach((section) =>
    section.classList.add("hidden")
  );

  // Apply class to clicked button and related section
  if (clickedButton === btn1) {
    btn1.classList.add(btnClass);
    section1.classList.remove("hidden");
  } else if (clickedButton === btn2) {
    btn2.classList.add(btnClass);
    section2.classList.remove("hidden");
  } else if (clickedButton === btn3) {
    btn3.classList.add(btnClass);
    section3.classList.remove("hidden");
  }
}

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

function changeHidden(id1, id2, className) {
  if (id1) document.getElementById(id1)?.classList?.remove("hidden");
  if (id2) document.getElementById(id2)?.classList?.add("hidden");

  if (className) {
    if (id1) document.getElementById(id1)?.classList?.add(className);
    if (id2) document.getElementById(id2)?.classList?.remove(className);
  }
}

function toggleHiddenData(dataKey, key, defaultState = null) {
  document.querySelectorAll(`tr[${dataKey}="${key}"]`).forEach((row) => {
    if (defaultState === null) {
      row.classList.toggle("hidden");
    } else if (defaultState === true) {
      row.classList.add("hidden");
    } else if (defaultState === false) {
      row.classList.remove("hidden");
    }
  });
}

function openLoader(title, id = "-pay-submit-", className = "block") {
  let spinner = document.getElementById("spinner" + id + title);
  if (spinner) spinner.style.display = className;
  let btn = document.getElementById("btn" + id + title);
  if (btn) btn.style.display = "none";

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";

  let form_errors = id + title + "-form-errors";
  if (form_errors.startsWith("-")) form_errors = form_errors.substring(1);
  if (document.getElementById(form_errors))
    document.getElementById(form_errors).innerHTML = "";
}

function closeLoader(title, id = "-pay-submit-", className = "block") {
  let spinner = document.getElementById("spinner" + id + title);
  if (spinner) spinner.style.display = "none";
  let btn = document.getElementById("btn" + id + title);
  if (btn) btn.style.display = className;

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";
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

let stripe, cardElement, elements, paymentElement;

function mountStripeCard(id) {
  const objEl = document.getElementById("stripe-element-" + id);
  const cardEl = document.getElementById("card-element-" + id);

  if (objEl && !cardEl) {
    mountStripeElement(id);
    return;
  }

  // unmount previous element
  // Unmount any existing elements
  if (cardElement) {
    cardElement.unmount();
    cardElement = null;
  }
  if (paymentElement) {
    paymentElement.unmount();
    paymentElement = null;
  }

  const lbl = document.getElementById("cardName-" + id);
  if (!stripe) {
    // const stripe_key = document
    //   .getElementById("contextData")
    //   .getAttribute("stripe_public_key");
    stripe = Stripe(stripe_public_key);
  }

  let color = "#fff";
  let placeholderColor = "rgb(156 163 175)";
  if (lbl) {
    color = lbl.style.color;
    let style = window.getComputedStyle(lbl);
    placeholderColor = window.getComputedStyle(lbl, "::placeholder").color;
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

        iconColor: color,
        "::placeholder": {
          color: placeholderColor,
        },
        ":focus": {
          border: "1px solid hsl(229, 76%, 72%);",
          "border-color": placeholderColor,
        },
      },
    },
  });

  cardElement.mount("#card-element-" + id);
}

function mountStripeElement(id, to_add = false, callback, bg_color = null) {
  const objEl = document.getElementById("stripe-element-" + id);
  const cardEl = document.getElementById("card-element-" + id);

  if (!objEl && cardEl) {
    mountStripeCard(id);
    return;
  }

  // unmount previous element
  // Unmount any existing elements
  if (cardElement) {
    cardElement.unmount();
    cardElement = null;
  }
  if (paymentElement) {
    paymentElement.unmount();
    paymentElement = null;
  }

  if (!stripe) {
    // const stripe_key = document
    //   .getElementById("contextData")
    //   .getAttribute("stripe_public_key");
    stripe = Stripe(stripe_public_key);
  }

  // 1) Request a new SetupIntent from your backend
  fetch("/my/membership/payment-intent/", {
    method: "POST",
    body: JSON.stringify({
      to_add: to_add,
      id: id,
    }),
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    credentials: "same-origin", // ensures cookies/session are sent
  })
    .then((response) => response.json())
    .then((payload) => {
      if (payload.error) {
        console.error("Failed to get client secret:", payload.error);
        return;
      }
      const clientSecret = payload.clientSecret;

      // print("Stripe client secret: " + clientSecret);
      const appearance = {
        theme: "stripe",
        variables: {
          fontFamily: '"Gill Sans", sans-serif',
          fontLineHeight: "1.5",
          borderRadius: "10px",

          colorBackground: getCssVariableColor("--color-background"),

          colorPrimary: getCssVariableColor("--color-primary"),
          colorText: getCssVariableColor("--color-text"),
          colorDanger: getCssVariableColor("--color-loss"),

          borderRadius: "6px",
          accessibleColorOnColorPrimary: "#262626",
          logoColor: "dark",
          tabLogoColor: "dark",
        },
        rules: {
          ".AccordionItem": {
            borderColor: getCssVariableColor("--color-text", 0.1),
            borderWidth: "2px",
            boxShadow: "none",
          },
          ".Block": {
            backgroundColor: "var(--colorBackground)",
            border: "none",
            boxShadow: "none",
            padding: "12px",
          },
          ".Input": {
            border: "2px solid " + getCssVariableColor("--color-text", 0),
            padding: "0.5rem 0.625rem",
            borderRadius: "0.375rem",
            backgroundColor: getCssVariableColor("--color-text", 0.1),
            // fontSize: "0.875rem",
          },
          ".Input::placeholder": {
            color: getCssVariableColor("--color-text", 0.4),
          },
          ".Input:disabled, .Input--invalid:disabled": {
            color: getCssVariableColor("--color-text", 0.4),
          },
          ".Tab": {
            padding: "10px 12px 8px 12px",
            border: "none",
          },
          ".Tab:hover": {
            border: "none",
            boxShadow:
              "0px 1px 1px rgba(0, 0, 0, 0.03), 0px 3px 7px rgba(18, 42, 66, 0.04)",
          },
          ".Tab--selected, .Tab--selected:focus, .Tab--selected:hover": {
            border: "none",
            backgroundColor: "var(--colorPrimary)",
            boxShadow:
              "0 0 0 1.5px var(--colorPrimaryText), 0px 1px 1px rgba(0, 0, 0, 0.03), 0px 3px 7px rgba(18, 42, 66, 0.04)",
          },
          ".Label": {
            fontWeight: "500",
          },
          ".Input:focus": {
            boxShadow: "0 0 0 0 transparent",
            outline: "1px solid transparent",
            border: "2px solid " + getCssVariableColor("--color-text", 0.4),
          },
        },
      };

      // console.log("Stripe client secret: " + clientSecret, appearance);

      elements = stripe.elements({ clientSecret, appearance, loader: "auto" });

      const paymentElementOptions = {
        layout: {
          type: "accordion",
          defaultCollapsed: false,
          // radios: false,
          spacedAccordionItems: true,
        },
        // Only offer Card and Cash App Pay:
        // paymentMethodOrder: ["card", "applepay", "googlepay", "cashapp"],

        // Hide the country and postal‐code sub‐fields on the card form:
        fields: {
          billingDetails: {
            address: {
              postalCode: "never", // never render the ZIP/postal field
              // country: "never", // never render the country‐select field
            },
          },
        },
      };

      paymentElement = elements.create("payment", paymentElementOptions);

      paymentElement.mount("#stripe-element-" + id);

      // Invoke callback if provided
      if (typeof callback === "function") callback();
    })
    .catch((err) => {
      console.error("Error creating SetupIntent:", err);
    });
}

function unmountStripeElement(title) {
  // unmount previous element
  // Unmount any existing elements
  if (cardElement) {
    cardElement.unmount();
    cardElement = null;
  }
  if (paymentElement) {
    paymentElement.unmount();
    paymentElement = null;
  }

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

async function onPayFormStripeElementSubmit(title) {
  openLoader(title, "-pay-submit-", "flex");

  const errorDiv = document.getElementById("stripe-error-" + title);
  if (errorDiv) errorDiv.innerHTML = "";

  // hide coupon errors
  if (document.getElementById(title + "-coupon-form-errors"))
    document.getElementById(title + "-coupon-form-errors").innerHTML = "";

  let coupon = document.getElementById("stripe-pay-coupon-" + title);
  if (coupon) {
    let coupon_val = document.getElementById("coupon-" + title).value;
    coupon.value = coupon_val;
  }

  const pmValue = document.getElementById("pm-" + title);

  const paymentsList = document.getElementById("payment-card-list-" + title);
  console.log("Checking card for " + title + " ... " + pmValue.value);

  if (
    pmValue.value.length === 0 ||
    pmValue.value === "None" ||
    (paymentsList && paymentsList.classList.contains("hidden"))
  ) {
    const { error, setupIntent } = await stripe.confirmSetup({
      //`Elements` instance that was used to create the Payment Element
      elements,
      confirmParams: {
        return_url: window.location.href,
        payment_method_data: {
          billing_details: {
            address: {
              // country: "US", // supply your ISO country code
              postal_code: "", // supply or leave empty to satisfy Stripe
            },
          },
        },
      },
      redirect: "if_required",
    });

    if (error) {
      // This point will only be reached if there is an immediate error when
      // confirming the payment. Show error to your customer (for example, payment
      // details incomplete)

      let errorHtml = `<div class="mx-auto text-sm flex p-4 text-error bg-error/5 border-2 border-error/40 rounded-md " role="alert"><svg class="flex-shrink-0 inline w-4 h-4 me-2 mt-[3px]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.929 4.929 19.07 19.071"/><circle cx="12" cy="12" r="10"/></svg><span class="sr-only">Error!</span><div><p>${error.message}</p></div>`;
      if (errorDiv) errorDiv.innerHTML = errorHtml;

      closeLoader(title);
      console.error("Stripe error:", error);
      return false;
    } else if (
      setupIntent.payment_method &&
      setupIntent.status === "succeeded"
    ) {
      pmValue.value = setupIntent.payment_method;
      // SetupIntent succeeded, proceed without redirect
      // console.log(
      //   "SetupIntent succeeded:",
      //   setupIntent.id,
      //   setupIntent.payment_method
      // );
    } else {
      closeLoader(title);
      console.error("SetupIntent succeeded but no payment method found.");
      return false;
    }
  }

  let form = document.getElementById("form-pay-" + title);
  form.dispatchEvent(new Event("submit"));

  // closeLoader(title);
  return true;
}

async function onPayFormStripeSubmit(title) {
  openLoader(title, "-pay-submit-", "flex");

  // hide coupon errors
  if (document.getElementById(title + "-coupon-form-errors"))
    document.getElementById(title + "-coupon-form-errors").innerHTML = "";

  const nameInput = document.getElementById("cardName-" + title);

  const pmValue = document.getElementById("pm-" + title);

  const paymentsList = document.getElementById("payment-card-list-" + title);
  console.log("Checking card for " + title + " ... " + pmValue.value);

  const errorDiv = document.getElementById("stripe-error-" + title);
  if (errorDiv) errorDiv.innerHTML = "";

  let coupon = document.getElementById("stripe-pay-coupon-" + title);
  if (coupon) {
    let coupon_val = document.getElementById("coupon-" + title).value;
    coupon.value = coupon_val;
  }

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
      let errorMsg =
        result.error.message + "\nNo payment method found or selected!";
      let errorHtml = `<div class="mx-auto text-sm flex p-4 text-error bg-error/10  rounded {{class}}" role="alert"><svg class="flex-shrink-0 inline w-4 h-4 me-3 mt-[2px]" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/></svg><span class="sr-only">Error!</span><div><p>${errorMsg}</p></div>`;
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

async function onAutomateAccountAdd(title, errorDivName, event) {
  event.preventDefault();

  openLoader("", "-add-" + title, "flex");

  if (document.getElementById("add-" + title + "-form-errors"))
    document.getElementById("add-" + title + "-form-errors").innerHTML = "";

  let form = document.getElementById("add-" + title + "-form");

  const nameInput = document.getElementById("cardName-" + title);
  const pmValue = document.getElementById("pm-" + title);

  const paymentsList = document.getElementById("payment-card-list-" + title);

  const errorDiv = document.getElementById(errorDivName);
  if (errorDiv) errorDiv.innerHTML = "";

  if (!pmValue && !paymentsList) {
    form.dispatchEvent(new Event("submit"));
    return true;
  }

  console.log("Checking card for " + title + " ... " + pmValue.value);
  if (
    pmValue.value.length === 0 ||
    pmValue.value === "None" ||
    (paymentsList && paymentsList.classList.contains("hidden"))
  ) {
    const { error, setupIntent } = await stripe.confirmSetup({
      //`Elements` instance that was used to create the Payment Element
      elements,
      confirmParams: {
        return_url: window.location.href,
        payment_method_data: {
          billing_details: {
            address: {
              // country: "US", // supply your ISO country code
              postal_code: "", // supply or leave empty to satisfy Stripe
            },
          },
        },
      },
      redirect: "if_required",
    });
    if (error) {
      let errorMsg = error.message + "\nNo payment method found or selected!";
      let errorHtml = `<div class="mx-auto text-sm flex p-4 text-error bg-error/10  rounded {{class}}" role="alert"><svg class="flex-shrink-0 inline w-4 h-4 me-3 mt-[2px]" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20"><path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/></svg><span class="sr-only">Error!</span><div><p>${errorMsg}</p></div>`;
      if (errorDiv) errorDiv.innerHTML = errorHtml;

      closeLoader(title, "-add-", "flex");
      return false;
    } else if (
      setupIntent.payment_method &&
      setupIntent.status === "succeeded"
    ) {
      pmValue.value = setupIntent.payment_method;
      // SetupIntent succeeded, proceed without redirect
      // console.log(
      //   "SetupIntent succeeded:",
      //   setupIntent.id,
      //   setupIntent.payment_method
      // );
    } else {
      closeLoader(title);
      console.error("SetupIntent succeeded but no payment method found.");
      return false;
    }
  }

  form.dispatchEvent(new Event("submit"));

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

function showModalImages(clickedImg, id = "") {
  // Derive the image list from the clicked image’s parent container
  const parent = clickedImg.parentElement;
  const imgElements = Array.from(parent.querySelectorAll("img"));
  const images = imgElements.map((imgEl, idx) => ({
    id: idx,
    imageUrl: imgEl.src,
  }));
  // Find the index of the clicked image
  const imgId = images.find((image) => image.imageUrl === clickedImg.src).id;

  const modalId = "modal-images-" + id;
  openModel(modalId);

  // Close the image modal on scroll
  // const scrollHandler = () => {
  //   hideModel(modalId);
  //   window.removeEventListener("wheel", scrollHandler, { passive: true });
  //   window.removeEventListener("touchmove", scrollHandler, { passive: true });
  // };
  // window.addEventListener("wheel", scrollHandler, { passive: true });
  // window.addEventListener("touchmove", scrollHandler, { passive: true });

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
    .getElementById("prev-button-carousel-" + id)
    .addEventListener("click", () => {
      currentIndex = (currentIndex - 1 + images.length) % images.length;
      showImage(currentIndex);
    });

  document
    .getElementById("next-button-carousel-" + id)
    .addEventListener("click", () => {
      currentIndex = (currentIndex + 1) % images.length;
      showImage(currentIndex);
    });

  if (images.length <= 1) {
    document
      .getElementById("prev-button-carousel-" + id)
      .classList.add("hidden");
    document
      .getElementById("next-button-carousel-" + id)
      .classList.add("hidden");
  } else {
    document
      .getElementById("prev-button-carousel-" + id)
      .classList.remove("hidden");
    document
      .getElementById("next-button-carousel-" + id)
      .classList.remove("hidden");
  }

  const carouselControl = document.getElementById("controls-carousel-" + id);
  const carouselContainer = document.getElementById("images-carousel-" + id);
  while (carouselContainer.firstChild) {
    carouselContainer.removeChild(carouselContainer.firstChild);
  }

  images.forEach((img, index) => {
    console.log(img);
    const imgElement = document.createElement("img");
    imgElement.src = img.imageUrl;
    imgElement.onclick = function () {
      hideModel(modalId);
    };
    imgElement.classList.add(
      "object-scale-down",
      "absolute",
      "max-w-[90%]",
      "max-h-[90%]",
      "aspect-auto",
      "block",
      "-translate-x-1/2",
      "-translate-y-1/2",
      "top-1/2",
      "left-1/2",
      "hover:cursor-zoom-out"
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

function openAITokensModalSettings(fromIsalgoAI = false) {
  openModel("staticModal-ai-tokens");
  mountStripeCard("ai-tokens");

  if (fromIsalgoAI === true) {
    const form = document.getElementById("add-ai-tokens-form");
    htmx.process(form);
  } else {
    const form = document.getElementById("add-ai-tokens-form");

    let newParam = "settings=true";
    let currentHxPost = form.getAttribute("hx-post");
    let newHxPost = currentHxPost + "?" + newParam;

    form.setAttribute("hx-post", newHxPost);
    htmx.process(form);
  }
}

function closeAITokensModalSettings() {
  hideModel("staticModal-ai-tokens");
  unmountStripeElement("ai-tokens");

  closeLoader("ai-tokens", "-add-", "flex");

  const form = document.getElementById("add-ai-tokens-form");

  if (form) {
    let currentHxPost = form.getAttribute("hx-post");
    let cleanHxPost = currentHxPost.split("?")[0];

    form.setAttribute("hx-post", cleanHxPost);
    htmx.process(form);
  }
}

// Select the tokens amount
let lastAiTokenId = "";

function AIamountBtnClick(id, amount, event) {
  console.log(amount);
  try {
    event.preventDefault(); // Prevent default button behavior

    const parts = id.split("-");
    // Grab everything between the first and last dash
    const title = parts.slice(1, -1).join("-");

    console.log(title, id);

    let activeClass = ["bg-text", "hover:bg-text", "text-background"];
    let desactiveClass = ["bg-text/10", "text-text", "hover:bg-text/20"];

    // Highlight the clicked button
    const btn = document.getElementById(id);
    btn.classList.remove(...desactiveClass);
    btn.classList.add(...activeClass);

    // Remove highlight from the last selected button
    if (lastAiTokenId && lastAiTokenId !== id) {
      const lastBtn = document.getElementById(lastAiTokenId);
      lastBtn.classList.remove(...activeClass);
      lastBtn.classList.add(...desactiveClass);
    }

    // Show input field if "Other" is selected, otherwise set amount
    let amountInput = document.getElementById("amount-" + title);
    if (Number(amount) <= 0) {
      document.getElementById("div-amount-" + title).classList.remove("hidden");
      amountInput.value = "";
      amountInput.focus();
    } else {
      amountInput.value = amount;
      document.getElementById("div-amount-" + title).classList.add("hidden");
    }

    lastAiTokenId = id;
  } catch (e) {
    console.error("amountBtnClick error:", e);
  }
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

  // if (evt?.detail?.target.id.includes("coupon-pay-")) {
  //   const title = evt?.detail?.target.id.replace("coupon-pay-", "");
  //   // closeLoader(title);

  // }

  // if (evt?.detail?.target.id.includes("stripe-next-")) {
  //   console.log("next ...");
  //   const title = evt?.detail?.target.id.replace("stripe-next-", "");
  //   closeLoader(title);

  //   changeHidden("submit-btn-sub-" + title, "submit-btn-next-" + title, "flex");

  //   const pmValue = document.getElementById("pm-" + title);
  //   if (pmValue) {
  //     const id1 = "payment-card-list-" + title;
  //     if (document.getElementById(id1)?.classList?.contains("hidden")) {
  //       pmValue.value = "None";
  //     }
  //   }
  // }

  if (
    evt?.detail?.target.id.includes("setting-ai-tokens") &&
    !evt?.detail?.target.id.includes("errors")
  ) {
    closeAITokensModalSettings();
  }

  if (
    evt?.detail?.target.id.includes("add-ai-tokens-form") &&
    !evt?.detail?.target.id.includes("errors")
  ) {
    closeAITokensModalSettings();
    // openModel("modal-algoai");
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

  if (evt?.detail?.target.id.includes("-form-errors")) {
    const name = "-" + evt?.detail?.target.id.replace("-form-errors", "");
    closeLoader("", name, "flex");
  }

  if (evt?.detail?.target.id.includes("at-accounts")) {
    const listId = document.getElementById("at-accounts-list");
    if (listId) {
      const modalId = listId.getAttribute("trigger-modal");
      if (modalId) hideModel(modalId);

      const btnId = listId.getAttribute("trigger-btn");
      if (btnId) closeLoader("", btnId, "flex");
    }

    hideModel("add-broker-modal");
  }

  const id = evt?.detail?.target.id;
  if (document.getElementById(id)) {
    const modalId = document.getElementById(id).hasAttribute("hide-backdrop");
    if (modalId) {
      const backdropDiv = document.querySelector("div[modal-backdrop]");
      if (backdropDiv) {
        backdropDiv.remove();
        document.documentElement.style.overflowY = "unset";
      }
    }
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
        { header: 1 }
      );
      fillSettingsFromSheet(propertiesSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Performance"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Performance"],
        { header: 1 }
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Trades analysis"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Trades analysis"],
        { header: 1 }
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["Risk performance ratios"]) {
      const performanceSheet = XLSX.utils.sheet_to_json(
        workbook.Sheets["Risk performance ratios"],
        { header: 1 }
      );
      fillResultsFromSheet(performanceSheet);
    }

    // Process results (Performance tab)
    if (workbook.Sheets["List of trades"]) {
      const listOfTrades = XLSX.utils.sheet_to_json(
        workbook.Sheets["List of trades"],
        { header: 1 }
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
          shortPerc
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
          shortPerc
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
          shortPerc
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
          trimPercentage(shortPerc)
        );
        break;
      case "max equity drawdown":
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
          shortPerc
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
          shortPerc
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
          shortPerc
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
  shortPerc = ""
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
  num = parseFloat(num) * 100;

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
  const dateIndex = header.indexOf("Date/Time");
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

function getNumberOfLines(id) {
  const element = document.getElementById(id);
  if (!element) return 0;
  let lineHeight = parseFloat(window.getComputedStyle(element).lineHeight);
  let totalHeight = element.scrollHeight;
  // console.log(totalHeight, totalHeight / lineHeight);
  return Math.round(totalHeight / lineHeight);
}

function sendAiMessage(message) {
  window.dispatchEvent(
    new CustomEvent("teroMessage", {
      detail: { message: message },
    })
  );
}

const modals = {};
function openModel(id, animated = true, backClose = true) {
  const modalElement = document.querySelector("#" + id);

  if (!modalElement) return false;

  let backdrop = "dynamic";
  if (!backClose) backdrop = "static";

  const modalOptions = {
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
      if (animated) {
        modalElement.classList.remove("scale-100"); // Remove full scale on hide
        // modalElement.classList.add("scale-0"); // Scale down when hiding
        // modalElement.classList.add("hidden");
      }
    },
    backdrop: backdrop,
    onShow: () => {
      document.querySelector("html").style.overflowY = "hidden";
      document.querySelector("body").classList.remove("overflow-hidden");
      modalElement.classList.remove("hidden"); // Show the modal
      if (animated) {
        setTimeout(() => {
          modalElement.classList.remove("scale-0"); // Start scaling up
          modalElement.classList.add("scale-100"); // Animate to full size
        }, 10); // Delay to allow for rendering
      }
      console.log("modal is shown");
    },
  };

  hideModel(id);
  // Initialize modal if it doesn't exist
  if (modals[id]) {
    modals[id].show();
  } else {
    if (animated) {
      modalElement.classList.add(
        "scale-0",
        "transition-transform",
        "duration-200",
        "ease-out"
      );
    }
    const modal = new Modal(modalElement, modalOptions);
    modals[id] = modal;
    modal.show();
  }
  return true;
}

function hideModel(id) {
  if (modals[id]) modals[id].hide();
  delete modals[id];

  return true;
}

const drawers = {};

function openDrawer(id, placement = "right") {
  const draweli = document.querySelector("#" + id);

  if (!draweli) return false;

  const drawerOptions = {
    placement: placement,

    backdrop: true,
    bodyScrolling: true,

    // backdrop: "dynamic",
    // backdropClasses: "bg-text/80 ",
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
      hideDrawer(id);
    },
    // onShow: () => {
    //   console.log("modal is shown");
    // },
    // onToggle: () => {
    //   console.log("modal has been toggled");
    // },
  };

  // hideDrawer(id);
  if (drawers[id]) drawers[id].show();
  else {
    const drawer = new Drawer(draweli, drawerOptions);
    drawers[id] = drawer;
    drawer.show();
  }

  document.querySelector("html").style.overflowY = "hidden";
  return true;
}

function hideDrawer(id) {
  const drawer = drawers[id];
  if (drawer) {
    delete drawers[id];
    drawer.hide();
  }

  return true;
}

// Custom dropdown open/close with animation and outside click handling
const customDropdownHandlers = {};

/**
 * Open a custom dropdown menu by its container ID.
 * Adds entry animation and sets up outside click listener.
 * @param {string} id - The dropdown container ID.
 */
function openCustomDropdown(id) {
  const menu = document.getElementById(id);
  if (!menu) return false;

  // If already open, do nothing
  if (!menu.classList.contains("hidden")) return false;

  // Apply initial animation styles
  menu.classList.remove("hidden");
  menu.classList.add(
    "opacity-0",
    "scale-95",
    "transition",
    "duration-200",
    "ease-out"
  );

  // Trigger reflow then animate to visible
  requestAnimationFrame(() => {
    menu.classList.remove("opacity-0", "scale-95");
    menu.classList.add("opacity-100", "scale-100");
  });

  // Outside‐click handler
  function outsideClickListener(e) {
    if (!menu.contains(e.target)) {
      closeCustomDropdown(id);
    }
  }

  // Store and—importantly—delay attaching the listener until
  // after the current click event has fully bubbled through.
  customDropdownHandlers[id] = outsideClickListener;
  setTimeout(() => {
    document.addEventListener("click", outsideClickListener);
  }, 0);

  return true;
}

/**
 * Close a custom dropdown menu by its container ID.
 * Adds exit animation and removes outside click listener.
 * @param {string} id - The dropdown container ID.
 */
function closeCustomDropdown(id) {
  const menu = document.getElementById(id);
  if (!menu) return false;

  // If already hidden, do nothing
  if (menu.classList.contains("hidden")) return false;

  // Animate to hidden state
  menu.classList.remove("opacity-100", "scale-100");
  menu.classList.add("opacity-0", "scale-95");

  // After animation ends, hide the element
  const handler = () => {
    menu.classList.add("hidden");
    menu.removeEventListener("transitionend", handler);
  };
  menu.addEventListener("transitionend", handler);

  // Remove outside click handler
  const outsideClickListener = customDropdownHandlers[id];
  if (outsideClickListener) {
    document.removeEventListener("click", outsideClickListener);
    delete customDropdownHandlers[id];
  }

  return true;
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

function openCtraderAuthWindow(clientIdInput, path) {
  const clientId =
    typeof clientIdInput === "string"
      ? document.getElementById(clientIdInput)
        ? document.getElementById(clientIdInput).value
        : clientIdInput
      : "";
  if (clientId) {
    const baseUrl = window.location.origin;
    const redirect_url = `${baseUrl}${path}`;
    const url = `https://id.ctrader.com/my/settings/openapi/grantingaccess?client_id=${clientId}&scope=trading&redirect_uri=${redirect_url}`;
    console.log("ctrader auth: ", url);
    window.open(
      url,
      "ctraderAuthWindow",
      "width=600,height=700,left=100,top=100"
    );
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Auto-play/pause videos on hover or touch within elements with class 'group'
  // Pause and reset all videos
  function pauseAllVideos() {
    document.querySelectorAll(".group video").forEach((v) => {
      v.pause();
      v.currentTime = 0;
    });
  }

  // Attach handlers to each group container
  document.querySelectorAll(".group").forEach((container) => {
    const video = container.querySelector("video");
    if (!video) return;

    // Play on hover
    container.addEventListener("mouseenter", () => {
      pauseAllVideos();
      video.play();
    });
    container.addEventListener("mouseleave", () => {
      video.pause();
      video.currentTime = 0;
      video.load();
    });

    // Play on touch for touchscreens
    container.addEventListener(
      "touchstart",
      () => {
        pauseAllVideos();
        video.play();
      },
      { passive: true }
    );
    container.addEventListener("touchend", () => {
      video.pause();
      video.currentTime = 0;
      video.load();
    });
  });

  const options = { root: null, rootMargin: "0px", threshold: 0.1 };
  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const delay = entry.target.getAttribute("animation-delay");
        if (delay) {
          entry.target.style.animationDelay = delay + "ms";
        }

        entry.target.classList.remove("opacity-0");
        entry.target.classList.add("animate-fade-up");
        obs.unobserve(entry.target);
      }
    });
  }, options);
  document.querySelectorAll(".fade-up-on-scroll").forEach((el) => {
    observer.observe(el);
  });
  const observer_dn = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const delay = entry.target.getAttribute("animation-delay");
        if (delay) {
          entry.target.style.animationDelay = delay + "ms";
        }

        entry.target.classList.remove("opacity-0");
        entry.target.classList.add("animate-fade-down");
        obs.unobserve(entry.target);
      }
    });
  }, options);
  document.querySelectorAll(".fade-down-on-scroll").forEach((el) => {
    observer_dn.observe(el);
  });
});
