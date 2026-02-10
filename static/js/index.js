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
    section.classList.add("hidden"),
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
        theme: "flat",
        variables: {
          fontFamily: '"Gill Sans", sans-serif',
          fontLineHeight: "1.5",
          borderRadius: "10px",

          colorBackground: "transparent",

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
            borderWidth: "1px",
            boxShadow: "none",
            backgroundColor: "transparent",
          },
          ".Block": {
            backgroundColor: "transparent",
            border: "none",
            boxShadow: "none",
            padding: "12px",
          },
          ".Tab": {
            padding: "10px 12px 8px 12px",
            border: "none",
            backgroundColor: "transparent",
          },
          ".TabLabel": {
            backgroundColor: "transparent",
          },
          ".TabIcon": {
            backgroundColor: "transparent",
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

async function submitStripeElementForm(title, errorDivName, event) {
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
      "add-payment_methods-close-form-btn",
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

  // if (evt?.detail?.target.id.includes("access-mb-")) {
  //   openModel("get-access-modal");
  //   const strategyId = evt?.detail?.target.id.replace("access-mb-", "");
  //   closeLoader("", "-acc-" + strategyId, "inline-flex");
  // }

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
    }),
  );
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
      "width=600,height=700,left=100,top=100",
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
      { passive: true },
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
