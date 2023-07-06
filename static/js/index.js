function openLoader(title) {
  document.getElementById("spinner-pay-submit-" + title).style.display =
    "block";
  document.getElementById("btn-pay-submit-" + title).style.display = "none";

  if (document.getElementById("error-pay-submit-" + title))
    document.getElementById("error-pay-submit-" + title).style.display = "none";
}
function closeLoader(title) {
  document.getElementById("spinner-pay-submit-" + title).style.display = "none";
  document.getElementById("btn-pay-submit-" + title).style.display = "block";
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

let stripe, cardElement;
stripe = Stripe(
  "pk_test_51NQMS2J5gHo8PE1NkuozkIhIpTZ04rH9zWLHdqqFwSTTPG3ciGfylBLolIdsaYnddawM6sN55JmoTuJCNjEQO4ST00JFXmLBeR"
);
const elements = stripe.elements();
console.log(elements);
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

function mountStripeElement(id) {
  cardElement.mount("#card-element-" + id);
}

function unmountStripeElement() {
  cardElement.unmount();
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

    closeLoader(title);
    return true;
  }
}
