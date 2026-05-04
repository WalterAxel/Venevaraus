(function () {
  function showErrorPopup(message) {
    var prev = document.getElementById("ajax-form-message");
    if (prev) {
      prev.remove();
    }
    var el = document.createElement("div");
    el.id = "ajax-form-message";
    el.setAttribute("role", "alert");
    el.textContent = message;
    el.style.cssText =
      "position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);" +
      "max-width:min(34rem,92vw);padding:0.9rem 1.25rem;background:#fff;" +
      "color:#c40000;border:2px solid #d32f2f;border-radius:10px;font:1.1rem system-ui,sans-serif;line-height:1.45;font-weight:600;" +
      "z-index:99999;box-shadow:0 6px 28px rgba(211,47,47,.25);text-align:center";
    document.body.appendChild(el);
  }

  function parseResponse(response) {
    var ct = response.headers.get("content-type") || "";
    if (ct.indexOf("application/json") !== -1) {
      return response.json().catch(function () {
        return { error: "Odottamaton vastaus palvelimelta." };
      });
    }
    return response.text().then(function () {
      return { error: "Odottamaton vastaus palvelimelta." };
    });
  }

  if (typeof fetch !== "function") {
    return;
  }

  document.querySelectorAll("form.ajax-form").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var confirmMsg = form.getAttribute("data-confirm");
      if (confirmMsg !== null) {
        if (!window.confirm(confirmMsg || "Oletko varma?")) {
          return;
        }
      }
      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then(parseResponse)
        .then(function (data) {
          if (data.redirect) {
            window.location.href = data.redirect;
            return;
          }
          if (data.error) {
            showErrorPopup(data.error);
            return;
          }
          showErrorPopup("Jotain meni pieleen.");
        })
        .catch(function () {
          showErrorPopup("Verkkovirhe. Yritä uudelleen.");
        });
    });
  });
})();
