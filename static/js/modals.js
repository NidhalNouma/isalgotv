/**
 * Modals, Drawers, and Dropdowns Management
 * Handles opening/closing of modals, drawers with stacking support, and custom dropdowns
 */

// =============================================================================
// MODALS
// =============================================================================

const modals = {};

/**
 * Open a modal by its ID
 * @param {string} id - The modal element ID
 * @param {boolean} animated - Whether to animate the modal
 * @param {boolean} backClose - Whether clicking backdrop closes the modal
 */
function openModel(id, animated = true, backClose = true) {
  const modalElement = document.querySelector("#" + id);

  if (!modalElement) return false;

  let backdrop = "dynamic";
  if (!backClose) backdrop = "static";

  const modalOptions = {
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
      if (animated) {
        modalElement.classList.remove("scale-100");
      }
    },
    backdrop: backdrop,
    onShow: () => {
      document.querySelector("html").style.overflowY = "hidden";
      document.querySelector("body").classList.remove("overflow-hidden");
      modalElement.classList.remove("hidden");
      if (animated) {
        setTimeout(() => {
          modalElement.classList.remove("scale-0");
          modalElement.classList.add("scale-100");
        }, 10);
      }
      console.log("modal is shown");
    },
  };

  hideModel(id);

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

/**
 * Hide a modal by its ID
 * @param {string} id - The modal element ID
 */
function hideModel(id) {
  if (modals[id]) modals[id].hide();
  delete modals[id];

  return true;
}

// =============================================================================
// DRAWERS
// =============================================================================

const drawers = {};

/**
 * Open a drawer by its ID
 * @param {string} id - The drawer element ID
 * @param {string} placement - Drawer placement (right, left, top, bottom)
 */
function openDrawer(id, placement = "right") {
  const drawerEl = document.querySelector("#" + id);

  if (!drawerEl) return false;

  const drawerOptions = {
    placement: placement,
    backdrop: true,
    bodyScrolling: true,
    onHide: () => {
      document.querySelector("html").style.overflowY = "unset";
      hideDrawer(id);
    },
  };

  if (drawers[id]) {
    drawers[id].show();
  } else {
    const drawer = new Drawer(drawerEl, drawerOptions);
    drawers[id] = drawer;
    drawer.show();
  }

  document.querySelector("html").style.overflowY = "hidden";
  return true;
}

/**
 * Hide a drawer by its ID
 * @param {string} id - The drawer element ID
 */
function hideDrawer(id) {
  const drawer = drawers[id];
  if (drawer) {
    delete drawers[id];
    drawer.hide();
  }
  return true;
}

// =============================================================================
// CUSTOM DROPDOWNS
// =============================================================================

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

  // Store and delay attaching the listener until
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
