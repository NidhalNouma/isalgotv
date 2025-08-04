const BASE = "/trade";

function getCookie(name) {
  const cookies = document.cookie.split(";").map((c) => c.trim());
  for (let c of cookies) {
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return null;
}

const csrf_token = getCookie("csrftoken");

export async function fetchAccounts() {
  const res = await fetch(`${BASE}/accounts/list/`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
  });
  return res.json();
}
