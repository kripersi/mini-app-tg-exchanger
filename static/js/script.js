const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

// === Проверка текущей страницы ===
document.addEventListener("DOMContentLoaded", () => {
  const navControl = document.getElementById("nav-control");
  const isIndexPage = window.location.pathname === "/" || window.location.pathname.endsWith("/index");

  if (isIndexPage && navControl) {
    navControl.innerHTML = `<div class="greeting-bar">Главное меню</div>`;
  }

  const countrySelect = document.getElementById("country");
  const giveSelect = document.getElementById("give_currency");
  const getSelect = document.getElementById("get_currency");
  const citySelect = document.getElementById("city");
  const form = document.getElementById("exchangeForm");

  const MIN_USDT = 5;
  const MAX_USDT = 100000;
  const COMMISSION_PERCENT = 3;

  const user = tg?.initDataUnsafe?.user;
  if (user) {
    document.querySelector('input[name="user_id"]').value = user.id || "";
    document.querySelector('input[name="first_name"]').value = user.first_name || "";
    document.querySelector('input[name="last_name"]').value = user.last_name || "";
    document.querySelector('input[name="username"]').value = user.username || "";
  }

  countrySelect?.addEventListener("change", async () => {
    const country = countrySelect.value;
    if (!country) return;

    try {
      const response = await fetch(`/api/country/${country}`);
      const data = await response.json();
      updateSelects(data);
    } catch (err) {
      console.error(err);
      showNotification("Не удалось загрузить данные страны.");
    }
  });

  function updateSelects(data) {
    giveSelect.innerHTML = "";
    getSelect.innerHTML = "";
    citySelect.innerHTML = "";

    const allCurrencies = [...data.currencies_from_crypto, ...data.currencies_from_fiat];

    allCurrencies.forEach((cur) => {
      giveSelect.append(new Option(cur, cur));
      getSelect.append(new Option(cur, cur));
    });

    data.cities.forEach((city) => {
      citySelect.append(new Option(city, city));
    });
  }

  function showNotification(message) {
    const container = document.getElementById("notification-container") || (() => {
      const el = document.createElement("div");
      el.id = "notification-container";
      document.body.appendChild(el);
      return el;
    })();

    const notif = document.createElement("div");
    notif.classList.add("notification");
    notif.textContent = message;
    container.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
  }

  let currentRate = null;

  async function updateRate() {
    const give = giveSelect.value;
    const get = getSelect.value;

    if (!give || !get || give === get) {
      currentRate = null;
      document.getElementById("exchange-section").style.display = "none";
      if (give === get) showNotification("Нельзя обменивать одинаковые валюты!");
      return;
    }

    try {
      const res = await fetch(`/get_rate?give_currency=${give}&get_currency=${get}`);
      const data = await res.json();

      if (data.rate) {
        currentRate = data.rate;
        const adjustedRate = data.rate * (1 - COMMISSION_PERCENT / 100);
        document.getElementById("rate-info").innerText = `1 ${give} ≈ ${adjustedRate.toFixed(4)} ${get}`;
        document.getElementById("exchange-section").style.display = "block";
      } else {
        currentRate = null;
        document.getElementById("rate-info").innerText = "Курс не найден.";
      }
    } catch (err) {
      console.error(err);
      currentRate = null;
      document.getElementById("rate-info").innerText = "Ошибка загрузки курса.";
    }
  }

  giveSelect.addEventListener("change", updateRate);
  getSelect.addEventListener("change", updateRate);

  document.getElementById("give-amount").addEventListener("input", async () => {
    if (!currentRate) return;

    const raw = document.getElementById("give-amount").value.replace(",", ".");
    const giveValue = parseFloat(raw);
    const getInput = document.getElementById("get-amount");
    const warning = document.getElementById("amount-warning");
    warning.textContent = "";

    if (isNaN(giveValue)) {
      getInput.value = "";
      return;
    }

    if (giveSelect.value !== "USDT" && giveSelect.value !== getSelect.value) {
      try {
        const res = await fetch(`/get_rate?give_currency=${giveSelect.value}&get_currency=USDT`);
        const data = await res.json();

        if (!data.rate) {
          warning.textContent = "Не удалось получить курс к USDT";
          return;
        }

        const usdtEquivalent = giveValue * data.rate * (1 - COMMISSION_PERCENT / 100);

        if (usdtEquivalent < MIN_USDT) {
          warning.textContent = `Сумма слишком мала: минимум 5 USDT (у вас ${usdtEquivalent.toFixed(4)} USDT)`;
        } else if (usdtEquivalent > MAX_USDT) {
          warning.textContent = `Сумма слишком большая: максимум 100000 USDT (у вас ${usdtEquivalent.toFixed(2)} USDT)`;
        }
      } catch (err) {
        console.error(err);
        warning.textContent = "Ошибка при проверке лимитов.";
      }
    }

    const finalAmount = giveValue * currentRate * (1 - COMMISSION_PERCENT / 100);
    getInput.value = finalAmount.toFixed(4);
  });

  document.getElementById("get-amount").addEventListener("input", () => {
    if (!currentRate) return;
    const getValue = parseFloat(document.getElementById("get-amount").value.replace(",", "."));
    const giveInput = document.getElementById("give-amount");

    if (!isNaN(getValue)) {
      const rawAmount = getValue / (1 - COMMISSION_PERCENT / 100);
      const giveValue = rawAmount / currentRate;
      giveInput.value = giveValue.toFixed(4);
    } else {
      giveInput.value = "";
    }
  });

  document.getElementById("datetime").addEventListener("input", () => {
    const input = document.getElementById("datetime");
    const warning = document.getElementById("datetime-warning");
    warning.textContent = "";

    const value = input.value;
    const isValidFormat = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value);
    if (!isValidFormat) {
      warning.textContent = "Неверный формат даты и времени.";
      return;
    }

    const selectedDate = new Date(value);
    const now = new Date();
    const oneYearLater = new Date();
    oneYearLater.setFullYear(now.getFullYear() + 1);

    if (selectedDate < now) {
      warning.textContent = "Дата уже прошла. Выберите будущую дату.";
    } else if (selectedDate > oneYearLater) {
      warning.textContent = "Дата слишком далёкая. Максимум — через 1 год.";
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const errorsContainer = document.getElementById("form-errors");
    const datetimeWarning = document.getElementById("datetime-warning");
    errorsContainer.innerHTML = "";
    datetimeWarning.textContent = "";

    try {
      const res = await fetch("/create", {
        method: "POST",
        body: formData
      });

      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, "text/html");
      const errorBlock = doc.querySelector("#form-errors");

      if (errorBlock && errorBlock.innerHTML.trim()) {
        errorsContainer.innerHTML = errorBlock.innerHTML;

        if (errorBlock.innerHTML.includes("Неверный формат даты и времени")) {
          datetimeWarning.textContent = "Неверный формат даты и времени.";
        }
      } else {
        document.body.innerHTML = html;
      }
    } catch (err) {
      errorsContainer.innerHTML = "<div class='flash-item error'>Ошибка отправки формы.</div>";
      console.error(err);
    }
  });
});
