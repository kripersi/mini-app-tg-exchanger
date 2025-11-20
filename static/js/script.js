const tg = window.Telegram?.WebApp;
if (tg) tg.expand();

document.addEventListener("DOMContentLoaded", async () => {
  const countrySelect = document.getElementById("country");
  const giveSelect = document.getElementById("give_currency");
  const getSelect = document.getElementById("get_currency");
  const citySelect = document.getElementById("city");
  const form = document.getElementById("exchangeForm");

  const MIN_USDT = 5;
  const MAX_USDT = 100000;
  const COMMISSION_PERCENT = 3;

  // --- Заполнение данных пользователя ---
  const user = tg?.initDataUnsafe?.user;
  if (user) {
    document.querySelector('input[name="user_id"]').value = user.id || "";
    document.querySelector('input[name="first_name"]').value = user.first_name || "";
    document.querySelector('input[name="last_name"]').value = user.last_name || "";
    document.querySelector('input[name="username"]').value = user.username || "";

    try {
      const resp = await fetch(`/api/user/${user.id}`);
      if (resp.ok) {
        const data = await resp.json();
        if (data.email) document.querySelector('input[name="email"]').value = data.email;
        if (data.full_name) document.querySelector('input[name="fullname"]').value = data.full_name;
      }
    } catch (err) {
      console.warn("Не удалось получить профиль пользователя:", err);
    }
  }

  // --- Функция уведомлений ---
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

  // --- debounce ---
  function debounce(fn, delay = 500) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  let currentRate = null;

  // --- Получение данных страны и валют ---
  async function fetchCountryData(country) {
    try {
      const res = await fetch(`/api/country/${country}`);
      const data = await res.json();
      if (data.error) {
        showNotification(data.error);
        return null;
      }
      return data;
    } catch (err) {
      console.error(err);
      showNotification("Ошибка загрузки данных страны");
      return null;
    }
  }

  countrySelect?.addEventListener("change", async () => {
    const country = countrySelect.value;
    if (!country) return;

    const data = await fetchCountryData(country);
    if (!data) return;

    const pairs = data.pairs || [];

    // уникальные валюты для отдачи
    const fromCurrencies = [...new Set(pairs.map(p => p.from))];
    giveSelect.innerHTML = '<option value="" disabled selected>Выберите валюту</option>';
    fromCurrencies.forEach(c => giveSelect.append(new Option(c, c)));

    // города
    citySelect.innerHTML = '<option value="" disabled selected>Выберите город</option>';
    data.cities.forEach(city => citySelect.append(new Option(city, city)));

    // очищаем get_currency и обменный блок
    getSelect.innerHTML = '<option value="" disabled selected>Выберите валюту</option>';
    document.getElementById("exchange-section").style.display = "none";
  });

  giveSelect?.addEventListener("change", async () => {
  const give = giveSelect.value;
  const country = countrySelect.value;
  if (!give || !country) return;

  const data = await fetchCountryData(country);
  if (!data) return;

  const pairs = data.pairs || [];

  // уникальные валюты для получения
  const possibleGets = [...new Set(pairs.filter(p => p.from === give).map(p => p.to))];

  getSelect.innerHTML = '<option value="" disabled selected>Выберите валюту</option>';
  possibleGets.forEach(c => getSelect.append(new Option(c, c)));

  document.getElementById("exchange-section").style.display = "none";
});


  getSelect?.addEventListener("change", async () => {
    const give = giveSelect.value;
    const get = getSelect.value;
    const country = countrySelect.value;
    if (!give || !get || !country) return;

    const data = await fetchCountryData(country);
    if (!data) return;

    const pair = data.pairs.find(p => p.from === give && p.to === get);
    if (!pair) {
      currentRate = null;
      document.getElementById("rate-info").innerText = "Пара не найдена.";
      document.getElementById("exchange-section").style.display = "none";
      return;
    }

    currentRate = pair.price;
    document.getElementById("rate-info").innerText = `1 ${give} ≈ ${currentRate.toFixed(4)} ${get}`;
    document.getElementById("exchange-section").style.display = "block";
  });

  // --- обработка ввода суммы ---
  const handleGiveAmountInput = async () => {
    if (!currentRate) return;

    const giveInputEl = document.getElementById("give-amount");
    const getInput = document.getElementById("get-amount");
    const warning = document.getElementById("amount-warning");

    const raw = giveInputEl.value.replace(",", ".");
    const giveValue = parseFloat(raw);
    warning.textContent = "";

    if (isNaN(giveValue)) {
      getInput.value = "";
      return;
    }

    const finalAmount = giveValue * currentRate * (1 - COMMISSION_PERCENT / 100);
    getInput.value = finalAmount.toFixed(4);

    // проверка лимитов через USDT, если есть курс
    try {
      const res = await fetch(`/api/rate_to_usdt?currency=${giveSelect.value}`);
      if (res.ok) {
        const data = await res.json();
        if (data.rate) {
          const usdtEquivalent = giveValue * data.rate * (1 - COMMISSION_PERCENT / 100);
          if (usdtEquivalent < MIN_USDT) warning.textContent = `Минимум 5 USDT (у вас ${usdtEquivalent.toFixed(4)} USDT)`;
          else if (usdtEquivalent > MAX_USDT) warning.textContent = `Максимум 100000 USDT (у вас ${usdtEquivalent.toFixed(2)} USDT)`;
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  document.getElementById("give-amount").addEventListener("input", debounce(handleGiveAmountInput, 600));

  document.getElementById("get-amount").addEventListener("input", () => {
    if (!currentRate) return;

    const getValue = parseFloat(document.getElementById("get-amount").value.replace(",", "."));
    const giveInput = document.getElementById("give-amount");

    if (!isNaN(getValue)) {
      const giveValue = getValue / (1 - COMMISSION_PERCENT / 100) / currentRate;
      giveInput.value = giveValue.toFixed(4);
    } else {
      giveInput.value = "";
    }
  });

  // --- проверка datetime ---
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

    if (selectedDate < now) warning.textContent = "Дата уже прошла. Выберите будущую дату.";
    else if (selectedDate > oneYearLater) warning.textContent = "Дата слишком далёкая. Максимум — через 1 год.";
  });

  // --- submit формы ---
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const errorsContainer = document.getElementById("form-errors");
    errorsContainer.innerHTML = "";

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
      } else {
        document.body.innerHTML = html;
      }
    } catch (err) {
      errorsContainer.innerHTML = "<div class='flash-item error'>Ошибка отправки формы.</div>";
      console.error(err);
    }
  });
});
