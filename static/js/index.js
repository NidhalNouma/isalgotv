function openLoader(title, id = "-pay-submit-") {
  document.getElementById("spinner" + id + title).style.display = "block";
  document.getElementById("btn" + id + title).style.display = "none";

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";
}
function closeLoader(title, id = "-pay-submit-") {
  document.getElementById("spinner" + id + title).style.display = "none";
  document.getElementById("btn" + id + title).style.display = "block";
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
  if (!stripe) {
    stripe = Stripe(
      "pk_test_51NQMS2J5gHo8PE1NkuozkIhIpTZ04rH9zWLHdqqFwSTTPG3ciGfylBLolIdsaYnddawM6sN55JmoTuJCNjEQO4ST00JFXmLBeR"
    );
    elements = stripe.elements();
    cardElement = elements.create("card", {
      hidePostalCode: true,
      style: {
        base: {
          color: "#fff",
          "font-size": "0.875rem",
          "line-height": "1.25rem",

          iconColor: "rgb(156 163 175)",
          "::placeholder": {
            color: "rgb(156 163 175)",
          },
          ":focus": {
            "border-color": "rgb(63 131 248);",
          },
        },
      },
    });
  }

  cardElement.mount("#card-element-" + id);
}

function unmountStripeElement(title) {
  cardElement.unmount();
  closeLoader(title);
}

async function onPayFormStripeSubmit(title) {
  openLoader(title);
  const nameInput = document.getElementById("cardName-" + title);

  const result = await stripe.createPaymentMethod({
    elements,
    params: {
      billing_details: {
        name: nameInput.value,
      },
    },
  });
  if (result.error) {
    console.log(`Payment failed: ${result.error.message}`);
    closeLoader(title);
    return false;
  } else {
    console.log(result);

    document.getElementById("pm-" + title).value = result.paymentMethod.id;

    let form = document.getElementById("form-pay-" + title);
    form.dispatchEvent(new Event("submit"));

    // closeLoader(title);
    return true;
  }
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
