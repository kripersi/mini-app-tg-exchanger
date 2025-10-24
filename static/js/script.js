const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

document.addEventListener("DOMContentLoaded", () => {
  const countrySelect = document.getElementById("country");
  const giveSelect = document.getElementById("give_currency");
  const getSelect = document.getElementById("get_currency");
  const citySelect = document.getElementById("city");
  const form = document.getElementById("exchangeForm");

  const MIN_USDT = 5;
  const MAX_USDT = 100000;
  const COMMISSION_PERCENT = 3;

  // ======== Telegram User Info ========
  const user = tg?.initDataUnsafe?.user;
  if (user) {
    document.querySelector('input[name="user_id"]').value = user.id || "";
    document.querySelector('input[name="first_name"]').value = user.first_name || "";
    document.querySelector('input[name="last_name"]').value = user.last_name || "";
    document.querySelector('input[name="username"]').value = user.username || "";
  }

  // ======== Страна → валюты и города ========
  if (countrySelect) {
    countrySelect.addEventListener("change", async () => {
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
  }

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

  // ======== Проверка одинаковых валют ========
  const validateCurrencies = () => {
    if (giveSelect.value && getSelect.value && giveSelect.value === getSelect.value) {
      showNotification("Нельзя обменивать одинаковые валюты!");
    }
  };
  giveSelect.addEventListener("change", validateCurrencies);
  getSelect.addEventListener("change", validateCurrencies);

  // ======== Уведомления ========
  function showNotification(message) {
    let container = document.getElementById("notification-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "notification-container";
      document.body.appendChild(container);
    }

    const notif = document.createElement("div");
    notif.classList.add("notification");
    notif.textContent = message;

    container.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
  }

  // ======== Курс и пересчёт ========
  let currentRate = null;

  document.querySelectorAll("#give_currency, #get_currency").forEach(select => {
    select.addEventListener("change", async () => {
      const give = giveSelect.value;
      const get = getSelect.value;

      if (give && get && give !== get) {
        document.getElementById("exchange-section").style.display = "block";

        try {
          const res = await fetch(`/get_rate?give_currency=${give}&get_currency=${get}`);
          const data = await res.json();

          if (data.rate) {
            currentRate = data.rate;
            const adjustedRate = data.rate * (1 - COMMISSION_PERCENT / 100);
            document.getElementById("rate-info").innerText =
              `1 ${give} ≈ ${adjustedRate.toFixed(4)} ${get}`;
          } else {
            currentRate = null;
            document.getElementById("rate-info").innerText = "Курс не найден.";
          }
        } catch (err) {
          console.error(err);
          currentRate = null;
          document.getElementById("rate-info").innerText = "Ошибка загрузки курса.";
        }
      } else {
        document.getElementById("exchange-section").style.display = "none";
        currentRate = null;
      }
    });
  });

  // ======== Пересчёт суммы и проверка лимитов ========
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

    const giveCurrency = giveSelect.value;

    try {
      const res = await fetch(`/get_rate?give_currency=${giveCurrency}&get_currency=USDT`);
      const data = await res.json();

      if (!data.rate) {
        warning.textContent = "Не удалось получить курс к USDT";
        return;
      }

      const rawUsdt = giveValue * data.rate;
      const usdtEquivalent = rawUsdt * (1 - COMMISSION_PERCENT / 100);

      if (usdtEquivalent < MIN_USDT) {
        warning.textContent = `Сумма слишком мала: минимум 5 USDT (у вас ${usdtEquivalent.toFixed(4)} USDT)`;
      } else if (usdtEquivalent > MAX_USDT) {
        warning.textContent = `Сумма слишком большая: максимум 100000 USDT (у вас ${usdtEquivalent.toFixed(2)} USDT)`;
      } else {
        warning.textContent = "";
      }

      const rawAmount = giveValue * currentRate;
      const commission = rawAmount * (COMMISSION_PERCENT / 100);
      const finalAmount = rawAmount - commission;

      getInput.value = finalAmount.toFixed(4);
    } catch (err) {
      console.error(err);
      warning.textContent = "Ошибка при проверке лимитов.";
    }
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

  // ======== Проверка даты и времени ========
  document.getElementById("datetime").addEventListener("input", () => {
    const input = document.getElementById("datetime");
    const warning = document.getElementById("datetime-warning");
    warning.textContent = "";

    const value = input.value;
    const isValid = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value);

    if (!isValid) {
      warning.textContent = "Неверный формат даты и времени.";
    }
  });

  // ======== AJAX-отправка формы ========
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

      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const errorBlock = doc.querySelector("#form-errors");

      if (errorBlock && errorBlock.innerHTML.trim()) {
        errorsContainer.innerHTML = errorBlock.innerHTML;

        if (errorBlock.innerHTML.includes("Неверный формат даты и времени")) {
          datetimeWarning.textContent = "Неверный формат даты и времени.";
        }
      } else {
        window.location.href = "/success";
      }
    } catch (err) {
      errorsContainer.innerHTML = "<div class='flash-item error'>Ошибка отправки формы.</div>";
      console.error(err);
    }
  });
});
