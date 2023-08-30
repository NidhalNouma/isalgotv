function swapDivBtn(id1, id2) {
  const btn1 = document.getElementById(id1 + "-btn");
  const btn2 = document.getElementById(id2 + "-btn");
  const div1 = document.getElementById(id1);
  const div2 = document.getElementById(id2);

  const btnClass1 = btn1.classList.toString(); // Convert class list to string
  const btnClass2 = btn2.classList.toString(); // Convert class list to string

  btnClass1.split(" ").forEach((className) => {
    btn1.classList.remove(className);
  });

  btnClass2.split(" ").forEach((className) => {
    btn2.classList.remove(className);
  });

  btnClass1.split(" ").forEach((className) => {
    btn2.classList.add(className);
  });

  btnClass2.split(" ").forEach((className) => {
    btn1.classList.add(className);
  });

  div1.classList.add("hidden");
  div2.classList.remove("hidden");
}

function openLoader(title, id = "-pay-submit-") {
  document.getElementById("spinner" + id + title).style.display = "block";
  document.getElementById("btn" + id + title).style.display = "none";

  if (document.getElementById("error" + id + title))
    document.getElementById("error" + id + title).style.display = "none";
}
function closeLoader(title, id = "-pay-submit-") {
  document.getElementById("spinner" + id + title).style.display = "none";
  document.getElementById("btn" + id + title).style.display = "block";

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
  // console.log(evt);

  if (evt?.detail?.target.id === "settingsDiv") {
    clearResultForm();
  }
  // check which element triggered the htmx request. If it's the one you want call the function you need
  //you have to add htmx: before the event ex: 'htmx:afterRequest'
});

function scrollToResult(resultId) {
  const resultElement = document.getElementById(`result-${resultId}`);

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
