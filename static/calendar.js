(function () {
  function parseBootstrap() {
    var raw = document.getElementById("vene-calendar-data");
    if (!raw || !raw.textContent.trim()) {
      return null;
    }
    try {
      return JSON.parse(raw.textContent);
    } catch (e) {
      return null;
    }
  }

  var monthNames = [
    "Tammikuu", "Helmikuu", "Maaliskuu", "Huhtikuu", "Toukokuu", "Kesäkuu",
    "Heinäkuu", "Elokuu", "Syyskuu", "Lokakuu", "Marraskuu", "Joulukuu"
  ];

  function boot() {
    var grid = document.getElementById("cal-grid");
    var titleEl = document.getElementById("cal-title");
    if (!grid || !titleEl) {
      return;
    }

    var bootstrap = parseBootstrap();
    if (!bootstrap) {
      return;
    }

    var reservations = bootstrap.reservations || [];
    var pickDates = !!bootstrap.pickDates;
    var colorByCategory = !!bootstrap.colorByCategory;

    function dayHasBooking(dayRes) {
      return dayRes.some(function (r) {
        return (r.category || "booking") === "booking";
      });
    }

    function dayHasFault(dayRes) {
      return dayRes.some(function (r) {
        return r.category === "fault_report";
      });
    }

    var now = new Date();
    var y = now.getFullYear();
    var m = now.getMonth();

    function mondayFirstOffset(date) {
      return (date.getDay() + 6) % 7;
    }

    function pad2(n) {
      return n < 10 ? "0" + n : String(n);
    }

    function isoDate(yy, mo, d) {
      return yy + "-" + pad2(mo + 1) + "-" + pad2(d);
    }

    function datePart(isoStr) {
      if (!isoStr) return "";
      return isoStr.slice(0, 10);
    }

    function reservationsForDay(yy, mo, d) {
      var dayStr = isoDate(yy, mo, d);
      return reservations.filter(function (r) {
        var s = datePart(r.start);
        var e = datePart(r.end);
        return dayStr >= s && dayStr <= e;
      });
    }

    function bookingTitle(r) {
      var kind = r.category_display || "Varaus";
      return r.title + " (" + kind + ", " + r.username + ")";
    }

    function render() {
      titleEl.textContent = monthNames[m] + " " + y;
      grid.innerHTML = "";

      var first = new Date(y, m, 1);
      var startPad = mondayFirstOffset(first);
      var daysInMonth = new Date(y, m + 1, 0).getDate();

      var i;
      for (i = 0; i < startPad; i++) {
        var empty = document.createElement("div");
        empty.className = "calendar-widget__cell calendar-widget__cell--empty";
        empty.setAttribute("role", "gridcell");
        grid.appendChild(empty);
      }

      var today = new Date();
      var isThisMonth = today.getFullYear() === y && today.getMonth() === m;

      for (var d = 1; d <= daysInMonth; d++) {
        var cell = document.createElement("div");
        cell.className = "calendar-widget__cell";
        cell.setAttribute("role", "gridcell");

        var dayRes = reservationsForDay(y, m, d);
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "calendar-widget__day";
        btn.textContent = String(d);
        btn.setAttribute("tabindex", "-1");

        if (dayRes.length) {
          if (colorByCategory) {
            var hv = dayHasBooking(dayRes);
            var hk = dayHasFault(dayRes);
            if (hv && hk) {
              cell.classList.add("calendar-widget__cell--mixed");
              btn.classList.add("calendar-widget__day--cat-mixed");
            } else if (hk) {
              cell.classList.add("calendar-widget__cell--fault");
              btn.classList.add("calendar-widget__day--cat-fault");
            } else {
              cell.classList.add("calendar-widget__cell--booking");
              btn.classList.add("calendar-widget__day--cat-booking");
            }
          } else {
            cell.classList.add("calendar-widget__cell--booked");
            btn.classList.add("calendar-widget__day--booked");
          }
          btn.classList.add("calendar-widget__day--inspect");
          btn.title = dayRes.map(bookingTitle).join("\n");
        }

        if (isThisMonth && d === today.getDate()) {
          btn.classList.add("calendar-widget__day--today");
        }

        if (pickDates && !dayRes.length) {
          btn.classList.add("calendar-widget__day--pick");
        }

        btn.addEventListener("click", function (yy, mm, dd) {
          return function () {
            var dr = reservationsForDay(yy, mm, dd);
            if (dr.length === 1) {
              window.location.href = "/reservation/" + dr[0].id;
              return;
            }
            if (dr.length > 1) {
              window.location.href = "/reservations/day/" + isoDate(yy, mm, dd);
              return;
            }
            if (pickDates) {
              var startEl = document.getElementById("start");
              var endEl = document.getElementById("end");
              if (!startEl || !endEl) return;
              var datePartStr = isoDate(yy, mm, dd);
              startEl.value = datePartStr;
              endEl.value = datePartStr;
            }
          };
        }(y, m, d));

        cell.appendChild(btn);
        grid.appendChild(cell);
      }
    }

    var prev = document.getElementById("cal-prev");
    var next = document.getElementById("cal-next");
    if (prev) {
      prev.addEventListener("click", function () {
        m--;
        if (m < 0) {
          m = 11;
          y--;
        }
        render();
      });
    }
    if (next) {
      next.addEventListener("click", function () {
        m++;
        if (m > 11) {
          m = 0;
          y++;
        }
        render();
      });
    }

    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
